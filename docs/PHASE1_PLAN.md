# Phase 1 Implementation Plan — Backend, ML Engine, Memory MCP Server

**Scope:** the minimum end-to-end slice that lets a user submit a job posting (text or file), get an explainable fraud prediction, and have the interaction persisted to the memory store for later retrieval. Everything else (FS/WebSearch/Notification/Analytics MCPs, Frontend, Admin dashboard, quizzes) is **Phase 2+** and called out in the roadmap at the bottom.

**Exit criteria for Phase 1:**
- `docker compose up backend ml-engine memory-mcp auth-mcp db-mcp postgres chromadb` brings up a healthy stack.
- `POST /api/v1/jobs/analyze` returns a prediction with SHAP explanations and persists the job + result.
- `POST /api/v1/jobs/analyze-file` accepts a PDF or PNG/JPG and returns the same shape.
- `GET /api/v1/me/context` returns the user's last N predictions + top similar known scams from ChromaDB.
- ≥80% unit test coverage on `ml-engine/app/pipeline/` and integration tests for the gateway→ml-engine→memory-mcp loop.

---

## Step 0 — Repo Bootstrap (½ day)
1. Create the directory layout from `ARCHITECTURE.md §3`.
2. Add `.env.example` with every variable the Phase-1 services will read (DB URLs, JWT secret, service token, Chroma host, model path).
3. Add a minimal `docker-compose.yml` with `postgres`, `mongodb` (logs only, optional in P1), `chromadb`, plus stubs for `backend`, `ml-engine`, `memory-mcp`, `auth-mcp`, `db-mcp`. Internal-only network `fjd-net`.
4. Add `pyproject.toml` per Python service using `uv` or `pip-tools`. Pin Python to `3.12`.
5. Add `Makefile` targets: `make up`, `make down`, `make test`, `make train`, `make fmt`.

**Deliverable:** `docker compose up` boots, all services answer `/healthz` with 200 (even though most endpoints are stubs).

---

## Step 1 — Internal API Contracts (½ day, before any feature work)
1. Write OpenAPI specs by hand into `docs/api-contracts/` for the Phase-1 services:
   - `ml-engine.yaml` (`/predict`, `/predict/file`, `/model/info`, `/healthz`)
   - `memory-mcp.yaml` (upsert, query, context, delete, healthz)
   - `auth-mcp.yaml` (signup, login, refresh, me, healthz)
   - `db-mcp.yaml` (users, jobs, predictions CRUD, healthz)
2. Generate Pydantic models for each spec into `backend/app/clients/<service>_models.py` using `datamodel-code-generator`.
3. Implement a thin `backend/app/clients/base.py` with httpx async client, retries, `X-Service-Token`, structured logging, and request-ID propagation.

**Deliverable:** typed clients exist; the backend can import them even though target services are stubs.

---

## Step 2 — `auth-mcp` (1 day)
1. FastAPI app with SQLAlchemy 2.x + asyncpg, Alembic migration `0001_users.py`.
2. Endpoints: `POST /signup`, `POST /login`, `POST /refresh`, `GET /me`. Argon2 hashing via `passlib[argon2]`.
3. JWT issuance: HS256, `access` 15 min, `refresh` 7 days. Public key/secret loaded from `.env`.
4. Unit tests: hashing, token round-trip, expiry, duplicate signup.
5. Healthcheck pings Postgres.

**Deliverable:** can sign up + log in via curl against the backend gateway.

---

## Step 3 — `db-mcp` (1 day)
1. FastAPI + SQLAlchemy. Alembic migrations for `jobs`, `predictions`, `reports`, `audit_log` (Phase-2 entities scaffolded but unused yet).
2. CRUD endpoints constrained to operations the gateway actually needs (no generic SQL).
3. Add a thin Mongo writer for `prediction_logs` (optional in P1, behind a feature flag).
4. Tests: schema migration up/down, basic CRUD round-trip, idempotent inserts on `job.sha256`.

**Deliverable:** the gateway can create a `job`, attach a `prediction`, and list them per user.

---

## Step 4 — `ml-engine` core pipeline (2–3 days)
**4a. Feature extractors** (`app/pipeline/`)
- `text_clean.py`: HTML strip, unicode normalize, language detect (`langdetect`).
- `salary.py`: regex out salary mentions → annualize → compare to `data/role_salary_ref.csv` (bundled). Output `salary_z_score`, `salary_unrealistic_flag`.
- `url_rules.py`: extract URLs, compute domain entropy, TLD risk score, gmail/telegram/whatsapp contact flags.
- `grammar.py`: spaCy `en_core_web_sm` tokenization + simple anomaly metrics (repeated punctuation, ALL-CAPS ratio, OOV ratio). Keep dependency footprint small — `language_tool_python` is **opt-in** (requires Java) behind a flag.
- `lexical.py`: TF-IDF over a curated scam lexicon (bundled `datasets/scam_lexicon.txt`).
- `pipeline.py`: composes the above into a feature dict + numpy vector.

**4b. Training script** (`app/models/train.py`)
- Loads `datasets/sample_jobs.csv` (must include ≥1k labeled rows; if real data unavailable we synthesize a stratified sample documented in `datasets/README.md`).
- Stratified train/val/test split. Feature vector built via the same `pipeline.py` used at inference.
- Trains `XGBClassifier` with `StratifiedKFold` CV. Records metrics (PR-AUC, F1, calibration) to `model_store/manifest.json`.
- Serializes model + feature names + version to `model_store/model_v{ts}.joblib`.
- CLI: `python -m app.models.train --data datasets/sample_jobs.csv --out model_store/`.

**4c. Inference server** (`app/server.py`)
- `POST /predict`: validate input → run `pipeline.transform` → model `predict_proba` → `shap.TreeExplainer` → top-K explanations with human-readable labels.
- `POST /predict/file`: multipart accept PDF/PNG/JPG. PDF → PyMuPDF text layer; raster fallback per page to Tesseract. Image → Tesseract. Text then goes through the same `/predict` codepath.
- `GET /model/info`: returns the manifest.
- `POST /model/reload`: admin-only via service-token + role claim; reloads the latest artifact.

**4d. Tests**
- Golden inputs for each feature extractor (known-fraud and known-legit fixtures).
- Snapshot test on `/predict` ensuring `label`, `score ∈ [0,1]`, `len(explanations) == 5`.
- OCR test using a synthetic PDF generated in the test fixture.

**Deliverable:** `curl -X POST :8100/predict -d '{"text": "..."}'` returns a JSON prediction with explanations; same for a PDF upload.

---

## Step 5 — `memory-mcp` (1.5 days)
1. FastAPI app wrapping ChromaDB's Python client (HTTP mode, pointing at the `chromadb` container).
2. Embeddings: default to `sentence-transformers/all-MiniLM-L6-v2` (CPU-friendly, no API key). Selectable via env var.
3. Collections seeded on first boot: `user_context`, `known_scams`, `articles`. `known_scams` seeded from `datasets/known_scams.jsonl` (bundled).
4. Endpoints per `ARCHITECTURE.md §6`. Include a `GET /context/{user_id}` that returns the user's last N upserts + top-K matches from `known_scams` for a supplied query embedding.
5. Tests: upsert + query round-trip; persistence survives container restart via mounted volume.

**Deliverable:** after a prediction, the backend can store `{user_id, job_text, label, score}` into `user_context` and immediately retrieve similar past entries.

---

## Step 6 — `backend` gateway wiring (1.5 days)
1. FastAPI app with routers: `auth`, `jobs`, `me`. (Reports / awareness / admin = Phase 2.)
2. Middleware: JWT auth dependency, request-ID, structured logging, CORS for the local frontend dev origin.
3. `POST /api/v1/jobs/analyze`:
   - Validate JWT → call `ml-engine /predict` → persist via `db-mcp` → upsert to `memory-mcp` `user_context` → return combined payload.
4. `POST /api/v1/jobs/analyze-file`: same pipeline but streams the multipart upload straight to `ml-engine /predict/file`.
5. `GET /api/v1/me/context`: returns recent predictions + similar known scams.
6. Healthchecks: gateway aggregates downstream `/healthz` and returns a single status.

**Deliverable:** an authenticated user can hit the gateway with a job posting and get back an explainable prediction stored against their account.

---

## Step 7 — Integration tests (1 day)
1. `docker-compose.test.yml` brings up `backend + ml-engine + memory-mcp + auth-mcp + db-mcp + postgres + chromadb`.
2. Pytest suite at `tests/integration/` that:
   - signs up + logs in;
   - submits a known-scam text and asserts `label == "fraud"` and SHAP includes a salary-related feature;
   - submits a clean posting and asserts `label == "legit"`;
   - uploads a small PDF and asserts the same shape;
   - calls `GET /me/context` and asserts the new record is there.
3. Wire the suite into CI (`make test-integration`).

**Deliverable:** green CI for the Phase-1 slice.

---

## Step 8 — Documentation (½ day)
1. `README.md` quick-start: `cp .env.example .env`, `make train`, `docker compose up`, sample curl commands.
2. `docs/ARCHITECTURE.md` (this doc) + `docs/PHASE1_PLAN.md` checked in.
3. `datasets/README.md` documenting the sample dataset, label definitions, and known limitations.

---

## Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Sample dataset too small or biased → poor model | Document this explicitly; ship metrics with the manifest; gate releases on minimum PR-AUC threshold. |
| Tesseract OCR quality on low-DPI images | Pre-process (deskew, threshold) via OpenCV before OCR; surface a `low_ocr_confidence` flag in the response. |
| spaCy/Tesseract image bloat | Use multi-stage Docker builds; only `ml-engine` carries those deps. |
| ChromaDB schema changes between versions | Pin the image tag; persist via named volume; add migration notes. |
| Service-token leaks | Tokens read from `.env` only; never logged; rotate on deploy. |

---

## Out of Scope for Phase 1 (roadmap)
- **Phase 2:** `fs-mcp` (report rendering), `websearch-mcp` (company verification), `notification-mcp` (email + WS fanout), Frontend MVP (login, submit job, view result, view history).
- **Phase 3:** Admin analytics dashboard (`analytics-mcp`), scam reporting workflow, Awareness Module (articles + quizzes), RAG-driven personalized advice using `memory-mcp` + LLM.
- **Phase 4:** Hardening (rate limiting, audit log UI, mTLS between services, Prometheus/Grafana, k8s Helm chart).

---

## Estimated effort
~8–10 engineering-days for one experienced engineer to reach Phase-1 exit criteria, assuming the dataset is available. Add ~2 days if we need to synthesize a labeled dataset from public sources.
