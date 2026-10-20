"""Check the monument photos and split them for training.

    python ml/recognizer/prepare_data.py --root /path/to/monuments

Reads monuments/raw/<label>/ and monuments/test/<label>/ (see the "Monument photos plan" doc), then:
1. skips files that aren't images or are smaller than --min-side pixels on the short side,
2. drops near-duplicate training photos (perceptual hash),
3. drops training photos that look like a test photo, so the test score stays honest,
4. splits raw/ into train and val per class (--val, default 15%),
and writes monuments/splits.csv (path, label, split) for the training notebook.
"""

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

import imagehash
from PIL import Image, UnidentifiedImageError

LABELS = ("giza_pyramids", "great_sphinx", "karnak_temple", "luxor_temple", "abu_simbel", "other")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
NEAR_DUPLICATE = 4  # hash distance: 0 = identical, <= 4 = same shot (resized, recompressed, burst)
TEST_LOOKALIKE = 6  # a bit looser between train and test: when in doubt, keep the test honest


def photo_hash(path: Path) -> imagehash.ImageHash | None:
    """None when the file isn't a readable image."""
    try:
        with Image.open(path) as img:
            img.load()
            return imagehash.phash(img.convert("RGB"))
    except (UnidentifiedImageError, OSError):
        return None


def short_side(path: Path) -> int:
    with Image.open(path) as img:
        return min(img.size)


def scan(folder: Path, min_side: int, warnings: list[str]) -> dict[str, list[tuple[Path, imagehash.ImageHash]]]:
    found: dict[str, list[tuple[Path, imagehash.ImageHash]]] = {label: [] for label in LABELS}
    if not folder.is_dir():
        warnings.append(f"missing folder {folder}")
        return found
    for sub in sorted(p for p in folder.iterdir() if p.is_dir()):
        if sub.name not in LABELS:
            warnings.append(f"unknown class folder {sub} (expected one of {', '.join(LABELS)})")
            continue
        for path in sorted(sub.iterdir()):
            if path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            h = photo_hash(path)
            if h is None:
                warnings.append(f"not a readable image: {path}")
            elif short_side(path) < min_side:
                warnings.append(f"too small (< {min_side}px): {path}")
            else:
                found[sub.name].append((path, h))
    return found


def drop_near_duplicates(photos, warnings: list[str]):
    kept: list[tuple[Path, imagehash.ImageHash]] = []
    for path, h in photos:
        twin = next((p for p, kh in kept if h - kh <= NEAR_DUPLICATE), None)
        if twin is not None:
            warnings.append(f"near-duplicate dropped: {path.name} (same shot as {twin.name})")
        else:
            kept.append((path, h))
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, required=True, help="the monuments/ folder")
    parser.add_argument("--val", type=float, default=0.15, help="share of each class kept for validation")
    parser.add_argument("--min-side", type=int, default=400, help="smallest allowed short side in pixels")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--strict", action="store_true", help="exit with an error when there are warnings")
    args = parser.parse_args()

    warnings: list[str] = []
    raw = scan(args.root / "raw", args.min_side, warnings)
    test = scan(args.root / "test", args.min_side, warnings)
    test_hashes = [(p, h) for photos in test.values() for p, h in photos]

    rng = random.Random(args.seed)
    rows: list[tuple[str, str, str]] = []
    for label in LABELS:
        photos = drop_near_duplicates(raw[label], warnings)
        clean = []
        for path, h in photos:
            twin = next((p for p, th in test_hashes if h - th <= TEST_LOOKALIKE), None)
            if twin is not None:
                warnings.append(f"training photo dropped, looks like test photo {twin.name}: {path.name}")
            else:
                clean.append(path)
        rng.shuffle(clean)
        n_val = round(len(clean) * args.val)
        rows += [(str(p.relative_to(args.root)), label, "val") for p in clean[:n_val]]
        rows += [(str(p.relative_to(args.root)), label, "train") for p in clean[n_val:]]
        rows += [(str(p.relative_to(args.root)), label, "test") for p, _ in test[label]]

    out = args.root / "splits.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "label", "split"])
        writer.writerows(sorted(rows))

    counts = Counter((label, split) for _, label, split in rows)
    print(f"{'class':<15}{'train':>7}{'val':>7}{'test':>7}")
    for label in LABELS:
        print(f"{label:<15}{counts[label, 'train']:>7}{counts[label, 'val']:>7}{counts[label, 'test']:>7}")
    print(f"\nwrote {out}")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
    return 1 if warnings and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
