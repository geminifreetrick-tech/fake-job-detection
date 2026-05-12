# Fake Job Detection and Awareness System — Technical Architecture

**Status:** Draft for review
**Phase covered:** All phases (high-level). Phase-1 detail lives in `PHASE1_PLAN.md`.

---

## 1. Goals and Non-Goals

### Goals
- Detect fraudulent job postings from raw text, PDF, or image inputs with explainable predictions.
- Educate end users via an Awareness Module (quizzes, articles, scam examples).
- Persist user interactions and predictions for RAG-style retrieval and personalization.
- Provide an admin analytics dashboard, scam reporting, and real-time alerts.
- Ship as a single `docker-compose up` deployable that orchestrates Frontend, Backend, ML Engine, and 7 internal microservices.

### Non-Goals (initial release)
- Federated learning, on-device inference, multi-tenant SaaS billing, mobile native apps.
- Live crawling of job boards at scale (we verify on demand, not bulk-scrape).
- Replacement for a SOC — this is an advisory + educational tool, not a takedown service.

---

## 2. Service Topology

All services run on a single internal Docker network (`fjd-net`) with **only** the Frontend and Backend exposed to the host. The 7 "MCP servers" are internal HTTP microservices reachable only from inside the network.

```
                  ┌─────────────────────────────────────────────┐
   Browser  ───►  │  Frontend (Vite/React)   :5173 (host)       │
                  └────────────┬────────────────────────────────┘
                               │  HTTPS / WSS
                  ┌────────────▼────────────────────────────────┐
                  │  Backend API Gateway (FastAPI)   :8000      │
                  │  - JWT auth, WebSockets, rate-limit         │
                  │  - Aggregates calls to internal services    │
                  └──┬───┬───┬───┬───┬───┬───┬───┬──────────────┘
                     │   │   │   │   │   │   │   │
        ┌────────────┘   │   │   │   │   │   │   └────────────┐
        ▼                ▼   ▼   ▼   ▼   ▼   ▼                ▼
   ┌─────────┐  ┌──────────┐ ┌─────┐ ┌──────┐ ┌──────┐ ┌──────────┐ ┌─────────┐
   │ ML Eng  │  │ Memory   │ │ FS  │ │ Web  │ │ DB   │ │ Notif    │ │ Auth    │
   │ (HTTP)  │  │ MCP      │ │ MCP │ │ MCP  │ │ MCP  │ │ MCP      │ │ MCP     │
   │ :8100   │  │ :8200    │ │:8300│ │:8400 │ │:8500 │ │:8600     │ │:8700    │
   └────┬────┘  └────┬─────┘ └──┬──┘ └──┬───┘ └──┬───┘ └────┬─────┘ └────┬────┘
        │            │          │       │        │           │            │
        ▼            ▼          ▼       ▼        ▼           ▼            ▼
   model_store/  Chroma     uploads/  Google   Postgres   SMTP/        Postgres
   (volume)      (volume)   reports/  CSE,     MongoDB    WebSocket    (users)
                                      WHOIS                fanout
                       ┌──────────────┐
                       │ Analytics MCP│ :8800  (reads from DB MCP, materializes
                       └──────────────┘         metrics into Postgres)
```

### Service inventory (10 containers + 3 datastores)
| # | Service | Image base | Port (internal) | Exposed to host |
|---|---|---|---|---|
| 1 | `frontend` | node:20-alpine | 5173 | yes |
| 2 | `backend` | python:3.12-slim | 8000 | yes |
| 3 | `ml-engine` | python:3.12-slim | 8100 | no |
| 4 | `memory-mcp` | python:3.12-slim | 8200 | no |
| 5 | `fs-mcp` | python:3.12-slim | 8300 | no |
| 6 | `websearch-mcp` | python:3.12-slim | 8400 | no |
| 7 | `db-mcp` | python:3.12-slim | 8500 | no |
| 8 | `notification-mcp` | python:3.12-slim | 8600 | no |
| 9 | `auth-mcp` | python:3.12-slim | 8700 | no |
| 10 | `analytics-mcp` | python:3.12-slim | 8800 | no |
| — | `postgres` | postgres:16 | 5432 | no |
| — | `mongodb` | mongo:7 | 27017 | no |
| — | `chromadb` | chromadb/chroma | 8000 | no |

> Note on "MCP": we use the term per the user's spec to mean "modular internal microservice." Communication is **HTTP/JSON** over the Docker network using a shared `mcp_client` library. This is **not** Anthropic's Model Context Protocol (which is intended for LLM↔tool integration). If true MCP is desired, only `memory-mcp` and `websearch-mcp` would also expose an MCP/JSON-RPC adapter — easy to add later without changing the HTTP contracts.

---

## 3. Repository Layout

```
fake-job-detection/
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PHASE1_PLAN.md
│   └── api-contracts/             # OpenAPI specs per service
├── backend/                       # FastAPI gateway
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                   # /auth /jobs /reports /awareness /admin
│   │   ├── core/                  # config, security, deps
│   │   ├── clients/               # typed clients for each MCP service
│   │   ├── schemas/
│   │   └── ws/                    # WebSocket hub
│   └── tests/
├── ml-engine/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── server.py              # FastAPI inference server
│   │   ├── pipeline/
│   │   │   ├── features.py        # NLP feature extractors
│   │   │   ├── salary.py
│   │   │   ├── url_rules.py
│   │   │   └── grammar.py
│   │   ├── models/
│   │   │   ├── train.py           # XGBoost + sklearn stacking
│   │   │   └── explain.py         # SHAP wrapper
│   │   └── ocr/
│   │       ├── pdf.py             # PyMuPDF
│   │       └── image.py           # Tesseract via pytesseract
│   ├── datasets/
│   │   ├── README.md
│   │   ├── sample_jobs.csv        # labeled sample (≥1k rows)
│   │   └── schema.json
│   ├── model_store/               # mounted volume; trained artifacts
│   └── tests/
├── mcp-servers/
│   ├── _common/                   # shared lib: http client, auth, logging
│   ├── memory/                    # ChromaDB-backed RAG + context
│   ├── filesystem/                # uploads + report generation (PDF)
│   ├── websearch/                 # Google CSE + WHOIS + DNS
│   ├── database/                  # Postgres + Mongo data-access layer
│   ├── notification/              # email + WebSocket fanout
│   ├── auth/                      # JWT issuance + user CRUD
│   └── analytics/                 # aggregations + materialized metrics
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── pages/                 # user + admin
│       ├── components/
│       ├── lib/api.ts             # generated from backend OpenAPI
│       └── ws/
└── infra/
    ├── postgres/init.sql
    ├── mongo/init.js
    └── grafana/ (optional)
```

---

## 4. Data Model (initial)

### Postgres (via `db-mcp` and `auth-mcp`)
- `users(id, email, password_hash, role, created_at, ...)`
- `jobs(id, user_id, raw_text, source_type, source_uri, created_at)`
- `predictions(id, job_id, label, score, explanation_json, model_version, created_at)`
- `reports(id, job_id, reporter_user_id, reason, status, created_at)`
- `quizzes(id, slug, title, payload_json)`
- `quiz_attempts(id, user_id, quiz_id, score, answers_json, created_at)`
- `articles(id, slug, title, body_md, tags, published_at)`
- `audit_log(id, actor_id, action, target_type, target_id, meta_json, ts)`

### MongoDB (via `db-mcp`)
- `prediction_logs` — full feature vectors, SHAP values, timings.
- `request_logs` — sanitized request/response envelopes.
- `awareness_events` — page views, quiz starts, article reads.

### ChromaDB (via `memory-mcp`)
- Collection `user_context` — embeddings of past jobs + outcomes per `user_id`.
- Collection `known_scams` — curated scam corpus for similarity recall.
- Collection `articles` — awareness content for RAG.

---

## 5. Detection Pipeline

```
input ──► [OCR if PDF/img] ──► normalize ──► feature extraction ──► model ──► SHAP ──► result
                                              │
                                              ├── salary realism (z-score vs role/region table)
                                              ├── URL heuristics (entropy, TLD, lookalike)
                                              ├── grammar anomalies (spaCy + language_tool_python optional)
                                              ├── contact channel risk (gmail/telegram/whatsapp flags)
                                              ├── company verification (websearch-mcp)
                                              ├── lexical scam markers (TF-IDF on curated dict)
                                              └── memory similarity (memory-mcp top-k known_scams)
```

- **Model:** stacking ensemble — `XGBoostClassifier` + `LogisticRegression` calibrator. Trained on labeled CSV; serialized with `joblib` to `model_store/model_vN.joblib` plus a `manifest.json` (version, metrics, feature list).
- **Explainability:** `shap.TreeExplainer` returns per-feature contributions; the API surfaces top 5 positive and negative contributors with human-readable labels.
- **OCR:** PDFs handled by PyMuPDF (text layer first, fallback to per-page raster → Tesseract). Images go straight to Tesseract via `pytesseract`. OCR runs inside `ml-engine` to keep the dependency footprint contained.

---

## 6. Internal API Contracts (summary)

All internal services speak HTTP/JSON, authenticated by a shared **service token** header `X-Service-Token` (rotated via `.env`). The backend gateway re-issues user JWTs but services never see raw user passwords.

### `ml-engine` — `:8100`
- `POST /predict` `{text, metadata?}` → `{label, score, explanations[], model_version}`
- `POST /predict/file` (multipart) → same shape; OCR handled server-side.
- `GET  /model/info` → `{version, trained_at, metrics, features}`
- `POST /model/reload` (admin) → reloads latest artifact.

### `memory-mcp` — `:8200`
- `POST /collections/{name}/upsert` `{ids[], documents[], metadatas[], embeddings?}`
- `POST /collections/{name}/query` `{query_texts[], n_results, where?}` → `{matches[]}`
- `GET  /context/{user_id}?limit=N` → recent interactions + similar known scams.
- `DELETE /collections/{name}/items` `{ids[]}`

### `fs-mcp` — `:8300`
- `POST /uploads` (multipart) → `{file_id, sha256, content_type, size}`
- `GET  /uploads/{file_id}` → stream
- `POST /reports/render` `{prediction_id}` → PDF report (uses prediction + memory context)

### `websearch-mcp` — `:8400`
- `POST /verify-company` `{name, website?}` → `{whois, dns, search_signals, score}`
- `POST /search` `{query, k}` → `{results[]}`

### `db-mcp` — `:8500`
- CRUD for the Postgres entities listed above + write-only endpoints for the Mongo log collections. Exposed as REST resources, no raw SQL surface area.

### `notification-mcp` — `:8600`
- `POST /notify` `{user_id, channel, template, payload}` (email + websocket)
- `WS /ws/{user_id}` — internal fanout (frontend connects through the backend gateway, not directly here).

### `auth-mcp` — `:8700`
- `POST /signup`, `POST /login` → `{access_token, refresh_token}`
- `POST /refresh`, `POST /logout`, `GET /me`

### `analytics-mcp` — `:8800`
- `GET /metrics/overview`, `GET /metrics/timeseries?metric=...`
- `POST /events` (ingest)

Each service ships its own OpenAPI spec at `/openapi.json` and a `/healthz`. The backend's `clients/` directory contains a small typed wrapper per service (Pydantic models mirroring the spec).

---

## 7. AuthN / AuthZ
- End-user JWT (HS256, short-lived access + refresh) issued by `auth-mcp`, validated at the backend gateway.
- Roles: `user`, `admin`. Admin-only routes guarded by gateway dependency.
- Service-to-service: shared `X-Service-Token` + network isolation (services not exposed to host). For Phase-2 we can swap to mTLS or SPIFFE.
- Secrets pulled from `.env` via `pydantic-settings`. `.env.example` documents every variable; no defaults for secrets.

---

## 8. Real-Time Alerts
- Backend exposes `WS /ws` (per-user). On connect, gateway authenticates the JWT, then subscribes to `notification-mcp` over an internal WebSocket or Redis pub/sub (Phase-2 may swap to Redis if fanout grows).
- Events: `prediction.completed`, `report.status_changed`, `admin.alert`.

---

## 9. Observability
- **Logs:** structured JSON to stdout, collected by `docker logs`. Request IDs propagated via `X-Request-ID`.
- **Metrics:** `/metrics` Prometheus endpoint per service (Phase-2 wires Prometheus + Grafana).
- **Tracing:** OpenTelemetry SDK installed but exporter disabled by default.

---

## 10. Testing Strategy
- **Unit:** pytest for each service (feature extractors, OCR shims, client wrappers, JWT logic).
- **Integration:** `docker compose -f docker-compose.test.yml up` spins backend + ml-engine + memory-mcp + db-mcp + postgres + chromadb; pytest hits the gateway end-to-end.
- **Contract:** schemathesis against each service's OpenAPI to catch drift.
- **ML:** held-out test set + threshold tests on precision/recall; model metrics gated in CI.
- **Frontend:** Vitest + Playwright smoke (login, upload, view result, take quiz).

---

## 11. Deployment
- `docker-compose.yml` is the source of truth for local + dev. Volumes for `pgdata`, `mongodata`, `chromadata`, `model_store`, `uploads`.
- Healthchecks on every service; backend's `depends_on` uses `service_healthy` so the gateway only starts once dependencies are ready.
- Production deploy out of scope here; the compose file maps cleanly to a Kubernetes Helm chart later.

---

## 12. Open Questions for Review
1. Confirm **ChromaDB** as the vector store (vs Qdrant/Weaviate/pgvector).
2. Confirm communication model: **internal HTTP microservices** (current proposal) vs **true MCP servers** (Anthropic protocol).
3. OAuth providers needed beyond email/password?
4. Web-search provider preference (Google CSE assumed; SerpAPI/Bing alternative).
5. Is an **admin SSO** requirement in scope for Phase 1, or can admin role be assigned via DB seed?
6. Hosting target for production (so we can size containers / pick managed Postgres).
