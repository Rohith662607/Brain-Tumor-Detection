# API_SETUP_GUIDE.md

**No API keys are required to run this project.** Everything — model
inference, the backend API, storage, experiment tracking — runs locally with
free/open-source tools (see `REBUILD_PLAN.md` → Technology Choices).

There is one placeholder worth knowing about if you later choose to extend
this yourself:

## Optional: cloud object storage (not used by default)

The backend stores uploads/annotated images/reports on the local filesystem
(`backend/storage/`) by default — no account needed. If you later want to
move storage off the local disk (e.g. for a multi-instance deployment), a
free option is **MinIO** (self-hosted, S3-compatible, open-source):

- Sign up / self-host: https://min.io/ (no account required to self-host via
  Docker; hosted options exist but aren't needed here)
- If you wire this in, the env vars would look like:
  ```
  MINIO_ENDPOINT=YOUR_MINIO_ENDPOINT_HERE
  MINIO_ACCESS_KEY=YOUR_ACCESS_KEY_HERE
  MINIO_SECRET_KEY=YOUR_SECRET_KEY_HERE
  ```
  paste into `backend/.env`. This is **not implemented** in the current
  backend (it uses local filesystem storage) — it's noted here only in case
  you outgrow local storage later.

No other integration in this project needs a key, token, or paid account.
