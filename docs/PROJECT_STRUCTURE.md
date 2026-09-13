# PROJECT_STRUCTURE.md

```
brain-tumor-detection/
├── README.md                      # start here
├── REBUILD_PLAN.md                 # full audit of the original project + rationale for every decision
├── DATASET_IMPROVEMENT_GUIDE.md    # dataset-specific findings + relabeling/expansion recommendations
├── API_SETUP_GUIDE.md              # confirms: no paid API keys needed anywhere
├── docker-compose.yml              # brings up backend + frontend together
├── .env.example                    # docker-compose variables
├── .dockerignore
│
├── docs/
│   ├── ARCHITECTURE.md             # system design + why it's split this way
│   ├── TRAINING_GUIDE.md           # hardware-specific training configs, reading results
│   ├── API_DOCUMENTATION.md        # narrative companion to FastAPI's auto /docs
│   └── DEPLOYMENT_GUIDE.md         # local / Docker / GPU / free-hosting instructions
│
├── ml/                              # Phase 1 — dataset + model, standalone (no web framework)
│   ├── README.md
│   ├── configs/config.yaml         # every path/hyperparameter — single source of truth
│   ├── data/
│   │   ├── prepare_dataset.py      # merges axial+coronal+sagittal, validates, writes data.yaml
│   │   ├── validate_dataset.py     # integrity checks (also importable standalone)
│   │   ├── raw/archive/            # <- put your extracted Kaggle dataset here (gitignored)
│   │   └── processed/              # <- prepare_dataset.py's output (gitignored)
│   ├── train.py
│   ├── evaluate.py
│   ├── predict.py                  # also the module backend/ imports run_inference() from
│   ├── export.py
│   ├── requirements.txt
│   └── runs/                       # <- training/eval/predict outputs land here (gitignored)
│
├── backend/                         # Phase 2 — FastAPI, imports ml/predict.py directly
│   ├── README.md
│   ├── Dockerfile
│   ├── .env.example
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # app entrypoint, lifespan model loading
│   │   ├── config.py                # settings (env-var driven)
│   │   ├── db.py                     # SQLModel table + session
│   │   ├── schemas.py                 # API response models
│   │   ├── inference_service.py        # the ONE place that talks to ultralytics
│   │   └── routers/
│   │       ├── detect.py               # POST /api/detect
│   │       ├── history.py               # history list/detail/delete, image/report serving
│   │       └── system.py                 # /api/model/info, /api/health
│   └── storage/                     # <- uploads/annotated/reports/app.db land here (gitignored)
│
└── frontend/                        # Phase 3 — Next.js, talks to backend only over HTTP
    ├── README.md
    ├── Dockerfile
    ├── .env.local.example
    ├── package.json
    ├── tailwind.config.ts            # design tokens (the reading-room palette)
    ├── app/
    │   ├── layout.tsx
    │   ├── globals.css
    │   ├── page.tsx                    # New scan
    │   ├── history/page.tsx
    │   └── model/page.tsx
    ├── components/
    │   ├── image-viewer.tsx             # signature reticle/overlay component
    │   ├── upload-dropzone.tsx
    │   ├── findings-panel.tsx
    │   ├── history-grid.tsx
    │   ├── nav-rail.tsx
    │   ├── verdict-badge.tsx
    │   └── ui/                            # button, card, badge
    └── lib/
        ├── api.ts                          # typed client, mirrors backend/app/schemas.py
        └── utils.ts
```

## Where things that no longer exist used to be

For context when comparing against the original archive (see
`REBUILD_PLAN.md` for the full audit): there is no `yolov5/` vendored repo
(replaced by the `ultralytics` pip package), no `gui.py`/`detect.py`
(replaced by `backend/` + `ml/predict.py`), no TF Object Detection API files
(`generate_tfrecord.py`, `pbtxtmaker.py`, `model_main_tf2.py` — replaced by
the single YOLOv11 pipeline per the Model Strategy decision), and no
duplicate `New (n)`/`my_experimentN` folders (the dataset prep script writes
one clean, validated copy).
