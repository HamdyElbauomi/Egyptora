"""Training, evaluation and export for the monument recognizer. Used by train.ipynb.

Flow: splits.csv (from prepare_data.py) -> baseline (DINOv2 + nearest photos, no training)
-> fine-tune ConvNeXt-Tiny -> temperature calibration on val -> report on test -> ONNX + labels.json.

The exported model answers like app/ai/recognizer.py: a label and a confidence. "other", or a
confidence under the threshold, means "not sure".
"""

import csv
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

LABELS = ("giza_pyramids", "great_sphinx", "karnak_temple", "luxor_temple", "abu_simbel", "other")
OTHER = LABELS.index("other")
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)  # ImageNet, what the pretrained models expect


def device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ---------- data ----------


def read_splits(root: Path) -> dict[str, list[tuple[Path, int]]]:
    """{"train": [(path, label index), ...], "val": [...], "test": [...]} from root/splits.csv."""
    splits: dict[str, list[tuple[Path, int]]] = {"train": [], "val": [], "test": []}
    with (root / "splits.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            splits[row["split"]].append((root / row["path"], LABELS.index(row["label"])))
    return splits


def make_transform(img_size: int, train: bool) -> transforms.Compose:
    """Training photos get random crops, flips and light changes so the model sees more variety."""
    if train:
        return transforms.Compose(
            [
                transforms.RandomResizedCrop(img_size, scale=(0.45, 1.0)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomRotation(8),
                transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.25, hue=0.03),
                transforms.ToTensor(),
                transforms.Normalize(MEAN, STD),
            ]
        )
    return transforms.Compose(
        [
            transforms.Resize(int(img_size * 1.14)),
            transforms.CenterCrop(img_size),
            transforms.ToTensor(),
            transforms.Normalize(MEAN, STD),
        ]
    )


class Photos(Dataset):
    def __init__(self, items: list[tuple[Path, int]], transform: transforms.Compose):
        self.items, self.transform = items, transform

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int):
        path, label = self.items[i]
        with Image.open(path) as img:
            return self.transform(img.convert("RGB")), label


def loaders(root: Path, img_size: int, batch_size: int = 32, workers: int = 2) -> dict[str, DataLoader]:
    splits = read_splits(root)
    return {
        name: DataLoader(
            Photos(items, make_transform(img_size, train=name == "train")),
            batch_size=batch_size,
            shuffle=name == "train",
            num_workers=workers,
            pin_memory=torch.cuda.is_available(),
        )
        for name, items in splits.items()
    }


def class_weights(items: list[tuple[Path, int]]) -> torch.Tensor:
    """Rarer classes count more in the loss, so 'other' (twice as many photos) doesn't dominate."""
    counts = np.bincount([label for _, label in items], minlength=len(LABELS)).astype(float)
    counts[counts == 0] = 1
    weights = counts.sum() / (len(LABELS) * counts)
    return torch.tensor(weights, dtype=torch.float32)


# ---------- baseline: no training, nearest photos ----------


@torch.no_grad()
def embed(model: nn.Module, loader: DataLoader, dev: torch.device) -> tuple[np.ndarray, np.ndarray]:
    """One normalized feature vector per photo + its label."""
    model.eval().to(dev)
    feats, labels = [], []
    for x, y in loader:
        f = model(x.to(dev))
        feats.append(nn.functional.normalize(f, dim=1).cpu().numpy())
        labels.append(y.numpy())
    return np.concatenate(feats), np.concatenate(labels)


def knn_probs(train_f: np.ndarray, train_y: np.ndarray, test_f: np.ndarray, k: int = 7) -> np.ndarray:
    """Each test photo votes with its k most similar training photos, weighted by similarity."""
    sims = test_f @ train_f.T
    top = np.argsort(-sims, axis=1)[:, :k]
    probs = np.zeros((len(test_f), len(LABELS)))
    for i, idx in enumerate(top):
        for j in idx:
            probs[i, train_y[j]] += max(sims[i, j], 0)
    probs /= np.clip(probs.sum(axis=1, keepdims=True), 1e-9, None)
    return probs


# ---------- fine-tuning ----------


@dataclass
class History:
    epochs: list[dict] = field(default_factory=list)
    best_epoch: int = -1
    best_val_f1: float = -1.0


def build_classifier(name: str = "convnext_tiny.fb_in22k_ft_in1k", pretrained: bool = True) -> nn.Module:
    return timm.create_model(name, pretrained=pretrained, num_classes=len(LABELS))


def _run_epoch(model, loader, dev, loss_fn, optimizer=None, scaler=None):
    training = optimizer is not None
    model.train(training)
    total, correct, loss_sum = 0, 0, 0.0
    all_pred, all_true = [], []
    for x, y in loader:
        x, y = x.to(dev), y.to(dev)
        with torch.set_grad_enabled(training), torch.autocast(dev.type, enabled=dev.type == "cuda"):
            logits = model(x)
            loss = loss_fn(logits, y)
        if training:
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        pred = logits.argmax(1)
        total += len(y)
        correct += (pred == y).sum().item()
        loss_sum += loss.item() * len(y)
        all_pred.append(pred.cpu())
        all_true.append(y.cpu())
    pred, true = torch.cat(all_pred).numpy(), torch.cat(all_true).numpy()
    return loss_sum / total, correct / total, f1_score(true, pred, average="macro")


def fine_tune(
    model: nn.Module,
    data: dict[str, DataLoader],
    out: Path,
    head_epochs: int = 3,
    full_epochs: int = 12,
    head_lr: float = 1e-3,
    full_lr: float = 1e-4,
    patience: int = 4,
) -> History:
    """Stage 1 trains only the new last layer (the pretrained part stays as is).
    Stage 2 trains everything with a small learning rate. The best epoch on val (macro F1) is saved to `out`."""
    dev = device()
    model.to(dev)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights(data["train"].dataset.items).to(dev), label_smoothing=0.1)
    scaler = torch.amp.GradScaler(enabled=dev.type == "cuda")
    history = History()
    epoch, waited = 0, 0

    head = model.get_classifier()
    for stage, epochs in (("head", head_epochs), ("full", full_epochs)):
        if stage == "head":
            for p in model.parameters():
                p.requires_grad = False
            for p in head.parameters():
                p.requires_grad = True
            optimizer = torch.optim.AdamW(head.parameters(), lr=head_lr, weight_decay=0.05)
        else:
            for p in model.parameters():
                p.requires_grad = True
            optimizer = torch.optim.AdamW(model.parameters(), lr=full_lr, weight_decay=0.05)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1))
        for _ in range(epochs):
            started = time.time()
            tr_loss, tr_acc, _ = _run_epoch(model, data["train"], dev, loss_fn, optimizer, scaler)
            va_loss, va_acc, va_f1 = _run_epoch(model, data["val"], dev, loss_fn)
            scheduler.step()
            row = {
                "epoch": epoch,
                "stage": stage,
                "train_loss": round(tr_loss, 4),
                "train_acc": round(tr_acc, 4),
                "val_loss": round(va_loss, 4),
                "val_acc": round(va_acc, 4),
                "val_f1": round(va_f1, 4),
                "seconds": round(time.time() - started, 1),
            }
            history.epochs.append(row)
            print(row)
            if va_f1 > history.best_val_f1:
                history.best_val_f1, history.best_epoch, waited = va_f1, epoch, 0
                torch.save(model.state_dict(), out)
            elif stage == "full":
                waited += 1
                if waited >= patience:
                    print(f"stopping early: val F1 hasn't improved for {patience} epochs")
                    break
            epoch += 1
    model.load_state_dict(torch.load(out, map_location=dev))
    return history


@torch.no_grad()
def logits_of(model: nn.Module, loader: DataLoader) -> tuple[np.ndarray, np.ndarray]:
    dev = device()
    model.eval().to(dev)
    out, labels = [], []
    for x, y in loader:
        out.append(model(x.to(dev)).float().cpu().numpy())
        labels.append(y.numpy())
    return np.concatenate(out), np.concatenate(labels)


def fit_temperature(logits: np.ndarray, labels: np.ndarray) -> float:
    """One number T that makes confidences honest: softmax(logits / T). Fitted on val, never on test."""
    t_log = torch.zeros(1, requires_grad=True)
    x, y = torch.tensor(logits), torch.tensor(labels)
    optimizer = torch.optim.LBFGS([t_log], lr=0.1, max_iter=100)

    def step():
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(x / t_log.exp(), y)
        loss.backward()
        return loss

    optimizer.step(step)
    return float(t_log.detach().exp())


def softmax(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    z = logits / temperature
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


# ---------- evaluation ----------


def answer(probs: np.ndarray, threshold: float) -> np.ndarray:
    """What the app would show: the label index, or -1 for "not sure" (other, or confidence under threshold)."""
    best = probs.argmax(1)
    sure = (probs.max(1) >= threshold) & (best != OTHER)
    return np.where(sure, best, -1)


def report(probs: np.ndarray, labels: np.ndarray, threshold: float) -> dict:
    """Numbers for the graduation report, computed on the test set."""
    pred = probs.argmax(1)
    shown = answer(probs, threshold)
    monument = labels != OTHER
    p, r, f, n = precision_recall_fscore_support(labels, pred, labels=range(len(LABELS)), zero_division=0)
    return {
        "accuracy": round(float((pred == labels).mean()), 4),
        "macro_f1": round(float(f1_score(labels, pred, average="macro")), 4),
        "per_class": {
            LABELS[i]: {
                "precision": round(float(p[i]), 4),
                "recall": round(float(r[i]), 4),
                "f1": round(float(f[i]), 4),
                "photos": int(n[i]),
            }
            for i in range(len(LABELS))
        },
        "confusion": confusion_matrix(labels, pred, labels=range(len(LABELS))).tolist(),
        "threshold": threshold,
        # What travelers would experience with this threshold:
        "monuments_recognized_correctly": round(float((shown[monument] == labels[monument]).mean()), 4)
        if monument.any()
        else None,
        "monuments_wrong_answer": round(float(((shown != -1) & (shown != labels))[monument].mean()), 4)
        if monument.any()
        else None,
        "other_photos_rejected": round(float((shown[~monument] == -1).mean()), 4) if (~monument).any() else None,
    }


def threshold_table(probs: np.ndarray, labels: np.ndarray, thresholds=(0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)):
    """For each threshold: right answers vs wrong answers vs "not sure", to pick the threshold."""
    rows = []
    for t in thresholds:
        shown = answer(probs, t)
        right = ((shown == labels) & (labels != OTHER)) | ((shown == -1) & (labels == OTHER))
        wrong = (shown != -1) & (shown != labels)
        rows.append(
            {
                "threshold": t,
                "right": round(float(right.mean()), 4),
                "wrong_answer": round(float(wrong.mean()), 4),
                "not_sure_on_monument": round(float(((shown == -1) & (labels != OTHER)).mean()), 4),
            }
        )
    return rows


# ---------- export ----------


def export(model: nn.Module, out_dir: Path, img_size: int, temperature: float, threshold: float, metrics: dict):
    """recognizer.onnx (photo -> logits) + labels.json (what the backend needs to turn logits into an answer)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    model.eval().cpu()
    dummy = torch.randn(1, 3, img_size, img_size)
    torch.onnx.export(
        model,
        (dummy,),
        out_dir / "recognizer.onnx",
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
        dynamo=False,
    )
    info = {
        "labels": list(LABELS),
        "other_label": "other",
        "img_size": img_size,
        "resize": int(img_size * 1.14),
        "mean": MEAN,
        "std": STD,
        "temperature": round(temperature, 4),
        "threshold": threshold,
        "test_metrics": metrics,
    }
    (out_dir / "labels.json").write_text(json.dumps(info, indent=2))
    return out_dir / "recognizer.onnx", out_dir / "labels.json"


def check_onnx(onnx_path: Path, torch_model: nn.Module, img_size: int) -> float:
    """Largest difference between the ONNX and PyTorch outputs on a random photo (should be tiny)."""
    import onnxruntime as ort

    x = torch.randn(2, 3, img_size, img_size)
    with torch.no_grad():
        expected = torch_model.eval().cpu()(x).numpy()
    got = ort.InferenceSession(str(onnx_path)).run(None, {"image": x.numpy()})[0]
    return float(np.abs(expected - got).max())
