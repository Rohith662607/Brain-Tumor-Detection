# TRAINING_GUIDE.md

Practical companion to `ml/README.md` — this focuses on getting a good
result on *this* dataset with *your* hardware, not just running the scripts.

## Before training: understand what you're training on

Run `python data/prepare_dataset.py --config configs/config.yaml --force`
first and read its printed class balance. On the actual dataset behind this
project, the merged split comes out roughly:

| split | images | boxes | negative (class 0) | positive (class 1) |
|---|---|---|---|---|
| train | ~760 | ~780 | ~48% | ~52% |
| val | ~130 | ~140 | ~38% | ~62% |
| test | ~220 | ~240 | ~64% | ~36% |

Two things worth knowing before you train:
- This is a **small** dataset by detection standards (hundreds, not
  thousands, of images). Expect to lean on a smaller model (`yolo11n`/`s`)
  and heavier regularization (the config's conservative augmentation) rather
  than a large model — with this little data, a big model overfits, it
  doesn't get smarter.
- The class balance **shifts between splits** (test skews toward "negative"
  hard-examples relative to train/val). That's a real signal your test-set
  metrics may look different from val — don't be surprised if test mAP is
  lower than val mAP; that's the dataset, not a bug.

## Hardware-specific configs

**Consumer GPU (8GB VRAM, e.g. RTX 3060/4060):**
```bash
python train.py --config configs/config.yaml --batch 16
```
Defaults (`yolo11s`, batch 16, imgsz 640) fit comfortably.

**Low VRAM / older GPU (4-6GB):**
```yaml
# configs/config.yaml
model:
  base_weights: "yolo11n.pt"
train:
  batch: 8
```

**Google Colab (free tier, T4 GPU):**
```bash
!git clone <your-repo>
%cd brain-tumor-detection/ml
!pip install -r requirements.txt -q
!python data/prepare_dataset.py --config configs/config.yaml --force
!python train.py --config configs/config.yaml --batch 16
```
Free-tier Colab sessions disconnect after ~12h and can idle-timeout sooner —
`train.py` writes checkpoints continuously to `runs/train/.../weights/last.pt`,
so re-run with `--resume` after a disconnect rather than starting over.
Mount Google Drive and point `train.project_dir` at a Drive path so
checkpoints survive a runtime reset.

**Kaggle Notebooks (free tier, P100/T4):**
Same as Colab; Kaggle's own dataset hosting is a good place to keep
`data/processed/` between sessions instead of re-running
`prepare_dataset.py` every time (it's deterministic given the same seed, but
no reason to redo the copy step).

**CPU only:**
```bash
python train.py --config configs/config.yaml --device cpu --epochs 1 --batch 4
```
Use this only to confirm the pipeline runs end to end (a few minutes). A real
150-epoch run on CPU is impractical — get to a Colab/Kaggle GPU for anything
beyond a smoke test.

## Reading the results

After training, check `runs/train/tumor_yolo11/`:
- `results.png` — loss/mAP curves. Watch for validation loss climbing while
  training loss keeps falling — classic overfitting, common on a dataset
  this size. If you see it: lower `model.base_weights` to `yolo11n`,
  increase `train.patience` down (stop earlier), or reduce `epochs`.
- `confusion_matrix.png` — with only 2 classes (negative/positive) plus
  background, check specifically how often "negative" (hard-negative,
  tumor-mimicking tissue) gets confused for "positive" (actual tumor) — that
  confusion is the whole point of the hard-negative class, so if the model
  isn't separating them, more/better hard-negative examples would help more
  than more epochs.
- `weights/best.pt` — selected by validation mAP, not the last epoch. This
  is the file to point `evaluate.py`/`predict.py`/the backend at.

## Then: run real evaluation, not the old accuracy formula

```bash
python evaluate.py --config configs/config.yaml --weights runs/train/tumor_yolo11/weights/best.pt --split test
```

Compare `mAP50` against the original project's reported 98.3% — they are
**not directly comparable numbers** (accuracy vs. mAP measure different
things), so don't expect them to match; use `evaluate.py`'s output as the new
baseline going forward, not a like-for-like replacement figure.
