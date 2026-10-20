# Monument recognizer

Fine-tunes an image model to recognize 5 monuments, plus an `other` class for everything else.
The photo collection rules and who collects what are in the team doc *Monument photos plan*.

| Class | Folder (`recognition_label`) |
| --- | --- |
| Pyramids of Giza | `giza_pyramids` |
| Great Sphinx | `great_sphinx` |
| Karnak Temple | `karnak_temple` |
| Luxor Temple | `luxor_temple` |
| Abu Simbel | `abu_simbel` |
| Anything else | `other` |

## Files

| File | What it does |
| --- | --- |
| `prepare_data.py` | Checks the photos, drops broken, tiny and duplicate ones, splits `raw/` into train and val, writes `splits.csv` |
| `monuments.py` | Data loading, the no-training baseline, fine-tuning, calibration, evaluation and ONNX export |
| `train.ipynb` | Runs everything step by step on Colab or Kaggle, with charts |

## Run it

1. Put the photos in Google Drive as `MyDrive/Egyptora/monuments/{raw,test}/<label>/`, named
   `<person>_<source>_<number>.jpg` (e.g. `p3_commons_0042.jpg`).
2. Open `train.ipynb` in Colab (File → Open notebook → GitHub), pick a T4 GPU, and Run all.
3. Results land in `monuments/runs/convnext_tiny/`: `recognizer.onnx`, `labels.json`, `training_curves.png`,
   `confusion_matrix.png`.

Check the photos on your own machine first:

```bash
pip install -r ml/recognizer/requirements.txt
python ml/recognizer/prepare_data.py --root path/to/monuments
```

Photos and model files are never committed (`*.pt` and `*.onnx` are in `.gitignore`).

## How the answer works

The model gives a probability for each of the 6 classes, made honest with temperature scaling on val.
The app answers "not sure" when the top class is `other` or its probability is under the threshold
chosen in the notebook. Plugging the model into `app/ai/recognizer.py` is the next step, agreed as a team.
