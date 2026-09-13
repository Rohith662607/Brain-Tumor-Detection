# DATASET_IMPROVEMENT_GUIDE.md

Findings specific to the dataset itself (see `REBUILD_PLAN.md` for the full
project audit). This covers what to do about them.

## What's actually good here

- Real, plane-labeled clinical MRI data (axial/coronal/sagittal T1WCE), not
  synthetic or scraped.
- Consistent YOLO-format normalized bounding boxes — verified during Phase 1
  (`data/validate_dataset.py`) with **zero integrity errors** across all
  1,116 merged images (761 train / 132 val / 223 test).
- A deliberate "negative" (hard-negative, tumor-mimicking tissue) class
  alongside "positive" (actual tumor) — this is a genuinely useful design
  choice for reducing false positives, not a labeling mistake, and it's
  worth keeping rather than collapsing to a single-class detector.

## Issues found

### 1. Class balance shifts across splits
Measured directly (Phase 1 dataset prep output):

| split | negative | positive |
|---|---|---|
| train | 49% | 51% |
| val | 38% | 62% |
| test | 64% | 36% |

The test split is meaningfully more "negative"-heavy than train/val. This
isn't necessarily wrong (it may reflect how the original data was collected),
but it means:
- Don't be alarmed if test recall on "positive" looks worse than val recall
  — there's relatively more chances to misclassify a hard-negative as
  positive-free real estate in that split.
- If you expand the dataset (see below), prioritize positive examples for
  the test split specifically to keep it representative of deployment
  conditions (presumably closer to real screening prevalence, not 50/50).

### 2. Duplicate/near-duplicate images and labels in the raw archive
The raw `Braintumourpart2.zip` contained ~40 duplicate `my_experimentN`
output folders and ~230 duplicate `New (n)`-named files (see `REBUILD_PLAN.md`
§2). These were **not** included in the Phase 1 merge (`prepare_dataset.py`
only reads the canonical `axial_t1wce_2_class/` etc. folders) — so this is
already handled, not a to-do. Worth deleting from your local copy of the raw
archive regardless, to avoid confusion in future audits.

### 3. Two label formats, one source of truth needed
The original project maintained YOLO `.txt` and Pascal VOC `.xml` labels as
separate, independently-editable trees (for the YOLO and TF-OD pipelines
respectively). Since the rebuilt pipeline is YOLO-only (see Model Strategy in
`REBUILD_PLAN.md`), **treat the YOLO `.txt` files as the only source of
truth** going forward. If you ever need another format, generate it with a
script, don't hand-maintain a second copy.

### 4. Small dataset size
~1,100 images total across three planes is workable for fine-tuning a
pretrained YOLOv11 (transfer learning, not training from scratch) but leaves
little room for a held-out test set that's both large and representative —
which is exactly what issue #1 shows happening.

## Relabeling recommendations

Only worth doing if `evaluate.py`'s per-class AP50 (see `TRAINING_GUIDE.md`)
shows a specific, consistent failure pattern after a real training run —
don't relabel speculatively:
- If **negative→positive confusion** is high (per the confusion matrix), the
  hard-negative examples may need tighter/more consistent box boundaries —
  loose boxes around tumor-mimicking tissue teach the model the wrong extent.
- If **small tumors are missed**, check whether those boxes are annotated at
  all consistently across the three planes, or whether small lesions were
  simply left unlabeled in some slices — this shows up as "background" images
  that should have had a positive box.

## Augmentation recommendations

Already applied conservatively in `ml/configs/config.yaml` (see the
`train.augment` section and its inline reasoning) — flip left-right yes,
flip up-down no (anatomically invalid), small rotation only, no hue jitter
(MRI is effectively grayscale). If you expand augmentation further, keep
that anatomical-plausibility constraint: an augmentation that a radiologist
would call "not a real MRI" is actively harmful here, not just noise.

## Dataset expansion strategies

- **More positive examples in the test split specifically** (see issue #1)
  before adding volume anywhere else — it directly improves how much you can
  trust `evaluate.py`'s numbers.
- **Public sources, no paid access required:**
  - Kaggle "Brain Tumor Object Detection Datasets" (the likely origin of this
    project's data) and related Kaggle brain-MRI datasets — check license
    terms per-dataset before merging.
  - TCIA (The Cancer Imaging Archive) — larger volumes, DICOM format
    (needs conversion to JPEG/PNG + YOLO boxes; out of scope for this guide,
    but note TCIA data typically has *segmentation* masks, not boxes — a mask
    can be converted to a tight bounding box via its extent, which is usually
    a better box than one drawn freehand).
  - Figshare brain MRI datasets — check annotation format per-dataset; several
    ship classification labels only (tumor/no-tumor), not boxes, so they're
    useful for pretraining/sanity-checks but not directly mergeable into this
    detection dataset without new box annotations.
- Whatever you add, run it through `data/validate_dataset.py` before merging
  — that's exactly what it's for.
