# Fake Job Detection and Awareness System

A full-stack platform that detects fraudulent job postings and helps users
recognize scams. This repository contains **Phase 1**: the FastAPI gateway, ML
detection engine, and the Memory MCP server, plus the minimal Auth and DB MCP
servers required for an end-to-end slice.

Architecture and roadmap:
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/PHASE1_PLAN.md](./docs/PHASE1_PLAN.md)

---

## Quick start

```bash
git clone <this-repo>
cd fake-job-detection
cp .env.example .env
# IMPORTANT: edit .env and replace the change-me secrets before running.

# Bring up the Phase-1 stack
docker compose up -d --build

# Wait ~30s for everything to come healthy, then check
curl http://localhost:8000/healthz
curl http://localhost:8000/api/v1/healthz | jq

# Sign up
curl -X POST localhost:8000/api/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"correct horse battery"}' | tee /tmp/tok.json

TOKEN=$(jq -r .access_token /tmp/tok.json)

# Analyze a text job posting
curl -X POST localhost:8000/api/v1/jobs/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text":"URGENT!!! Work from home – earn $5000/week. Contact via Telegram @hire. $49 registration fee."}' | jq

# Analyze a PDF/PNG/JPG
curl -X POST localhost:8000/api/v1/jobs/analyze-file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/posting.pdf" | jq

# See your history + similar known scams
curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/v1/me/context | jq
```

---

## Services in this repo

| Service           | Path                       | Port (internal) | Exposed |
|-------------------|----------------------------|-----------------|---------|
| Backend gateway   | `backend/`                 | 8000            | yes     |
| ML engine         | `ml-engine/`               | 8100            | no      |
| Memory MCP        | `mcp-servers/memory/`      | 8200            | no      |
| Auth MCP          | `mcp-servers/auth/`        | 8700            | no      |
| Database MCP      | `mcp-servers/database/`    | 8500            | no      |
| Postgres          | (docker image)             | 5432            | no      |
| ChromaDB          | (docker image)             | 8000            | no      |

Phase 2+ adds Frontend (Vite/React), File-System MCP, Web-Search MCP,
Notification MCP, and Analytics MCP. See
[docs/PHASE1_PLAN.md](./docs/PHASE1_PLAN.md#out-of-scope-for-phase-1-roadmap).

---

## Configuration

All configuration is via `.env`. See [.env.example](./.env.example) for the
full set. Two values **must** be changed before deploying:

- `SERVICE_TOKEN` — shared secret for internal service-to-service auth.
- `JWT_SECRET` — HMAC key used by `auth-mcp` to sign user access tokens.

The backend gateway decodes user JWTs locally using the same secret as
`auth-mcp`, so the two values must match.

---

## Detection model

The ML engine implements the following feature extractors
(`ml-engine/app/pipeline/`):

| Group     | Features                                                          |
|-----------|-------------------------------------------------------------------|
| Salary    | `salary_z_score`, `salary_unrealistic_flag`                        |
| URLs      | `num_urls`, `url_suspicious_tld`, `url_max_entropy`, `url_brand_lookalike` |
| Contact   | `contact_free_email`, `contact_telegram`, `contact_whatsapp`        |
| Grammar   | `caps_ratio`, `repeat_punct_ratio`, `oov_ratio`, `exclaim_density`, `num_tokens` |
| Lexical   | `scam_marker_count`, `scam_marker_score`, `asks_for_payment`        |

The classifier is `XGBClassifier` trained on
[`ml-engine/datasets/sample_jobs.csv`](./ml-engine/datasets/) (synthetic, 1000
rows; see [`datasets/README.md`](./ml-engine/datasets/README.md) for caveats
and how to swap in a real dataset).

Explainability uses `shap.TreeExplainer`; the API surfaces the top-5 features
by absolute SHAP contribution with a human-readable label and direction
(fraud vs legit).

### Re-training

```bash
# Inside the ml-engine container (or your local venv):
python -m app.models.train --data datasets/sample_jobs.csv --out model_store/
# Then reload the live model without restarting:
curl -X POST http://localhost:8100/model/reload   # (internal only)
```

The image build runs the training step so the container is usable
out-of-the-box without a pre-existing volume.

### OCR

`POST /predict/file` accepts PDF / PNG / JPG:
- PDFs are first parsed via PyMuPDF's text layer; if empty, each page is
  rasterized and run through Tesseract.
- Images go straight through Tesseract.
- Plain text is passed through unchanged.

---

## Internal API contracts

See [docs/ARCHITECTURE.md §6](./docs/ARCHITECTURE.md#6-internal-api-contracts-summary)
for the full list. All internal services require the `X-Service-Token` header
and are not exposed on the host network. Each service publishes its own
OpenAPI spec at `/openapi.json` and a `/healthz` probe.

---

## Tests

```bash
# Per-service unit tests
make test-unit

# Or individually
cd ml-engine && pip install -e ".[test]" && pytest -q
cd mcp-servers/auth && pip install -e ".[test]" && pytest -q
cd mcp-servers/database && pip install -e ".[test]" && pytest -q
cd mcp-servers/memory && pip install -e ".[test]" && pytest -q
cd backend && pip install -e ".[test]" && pytest -q
```

### End-to-end smoke (docker-compose)

```bash
docker compose up -d --build
sleep 30
curl -fsS localhost:8000/api/v1/healthz | jq

# Sign up + analyze a known-scam text
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"smoketest@example.com","password":"correct horse battery"}' | jq -r .access_token)

curl -s -X POST localhost:8000/api/v1/jobs/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text":"URGENT!!! Work from home, earn $5000/week, contact via Telegram @hire, $49 registration fee"}' | jq '.label, .score'
```

You should see `"fraud"` and a probability ≥ 0.6.

---

## Project layout

```
fake-job-detection/
├── README.md
├── docker-compose.yml
├── .env.example
├── Makefile
├── docs/
│   ├── ARCHITECTURE.md
│   └── PHASE1_PLAN.md
├── backend/                       # FastAPI gateway (Phase 1)
├── ml-engine/                     # ML detection engine + OCR
│   ├── app/pipeline/              # feature extractors
│   ├── app/models/                # train + SHAP
│   ├── app/ocr/                   # PDF/image text extraction
│   └── datasets/                  # bundled training data + lexicon
├── mcp-servers/
│   ├── _common/                   # shared http + logging + security helpers
│   ├── auth/                      # JWT issuance + user CRUD
│   ├── database/                  # Postgres CRUD for jobs/predictions
│   └── memory/                    # ChromaDB-backed RAG + user context
├── infra/
│   └── postgres/init.sql
└── tests/integration/             # docker-compose end-to-end (Phase 1 stub)
```

---

## What's *not* in this repo yet

This is Phase 1. Deferred to subsequent phases (see `docs/PHASE1_PLAN.md`):

- Frontend (Vite/React/Tailwind/Recharts dashboard)
- File-System MCP (uploads + PDF report rendering)
- Web-Search MCP (company verification: Google CSE + WHOIS)
- Notification MCP (email + WebSocket fanout)
- Analytics MCP (aggregated metrics)
- Admin dashboard & scam-reporting workflow
- Awareness Module (articles + quizzes)
- mTLS / Prometheus / Grafana / k8s Helm chart

---

## License

Proprietary — internal use only unless otherwise stated.
