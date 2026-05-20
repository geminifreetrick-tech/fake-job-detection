# Fake Job Detection and Awareness System

A full-stack platform that detects fraudulent job postings, verifies the
companies behind them, and educates users on the patterns scammers use.

**Status: Phase 1 + Phase 2 complete** — full stack (frontend + backend +
9 internal services) orchestrated via `docker compose`.

Architecture and roadmap:
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- [docs/PHASE1_PLAN.md](./docs/PHASE1_PLAN.md)
- [docs/PHASE2_PLAN.md](./docs/PHASE2_PLAN.md)

---

## Quick start

```bash
git clone https://github.com/geminifreetrick-tech/fake-job-detection.git
cd fake-job-detection
cp .env.example .env
# IMPORTANT: edit .env and replace the change-me secrets before running.
# Optional: set BOOTSTRAP_ADMIN_EMAIL/PASSWORD to auto-create an admin user.

docker compose up -d --build

# Wait ~30s for everything to come healthy, then check
curl http://localhost:8000/healthz
curl http://localhost:8000/api/v1/healthz | jq

# Open the frontend
open http://localhost:5173       # macOS
xdg-open http://localhost:5173   # Linux
```

The Vite-built React frontend is served on `http://localhost:5173` and proxies
`/api/*` and `/ws` requests to the FastAPI gateway in the same compose network.

### API usage from cURL

```bash
# Sign up
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"correct horse battery"}' \
  | jq -r .access_token)

# Analyze a text job posting
curl -X POST localhost:8000/api/v1/jobs/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"text":"URGENT!!! Work from home – earn $5000/week. Contact via Telegram @hire. $49 registration fee."}' | jq

# Analyze a PDF/PNG/JPG
curl -X POST localhost:8000/api/v1/jobs/analyze-file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/posting.pdf" | jq

# Verify a company
curl -X POST localhost:8000/api/v1/companies/verify \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme Corporation","domain":"acme.com"}' | jq

# Submit a scam report
curl -X POST localhost:8000/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Fake recruiter on LinkedIn","description":"…","company":"Acme"}' | jq

# Generate a PDF report for an analysed job
curl -X POST localhost:8000/api/v1/files/reports/<job_id> \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Services in this repo

| Service             | Path                         | Internal port | Exposed | Phase |
|---------------------|------------------------------|---------------|---------|-------|
| Frontend            | `frontend/`                  | 80            | **5173**| 2     |
| Backend gateway     | `backend/`                   | 8000          | **8000**| 1     |
| ML engine           | `ml-engine/`                 | 8100          | no      | 1     |
| Memory MCP          | `mcp-servers/memory/`        | 8200          | no      | 1     |
| Notification MCP    | `mcp-servers/notification/`  | 8300          | no      | 2     |
| Filesystem MCP      | `mcp-servers/filesystem/`    | 8400          | no      | 2     |
| Database MCP        | `mcp-servers/database/`      | 8500          | no      | 1     |
| Web-search MCP      | `mcp-servers/websearch/`     | 8600          | no      | 2     |
| Auth MCP            | `mcp-servers/auth/`          | 8700          | no      | 1     |
| Analytics MCP       | `mcp-servers/analytics/`     | 8800          | no      | 2     |
| Postgres            | (docker image)               | 5432          | no      | 1     |
| ChromaDB            | (docker image)               | 8000          | no      | 1     |

Only the backend gateway (8000) and the frontend (5173) are published to the
host. Everything else is reachable only on the internal `fjd-net` Docker
network and gated by the `X-Service-Token` header.

---

## Configuration

All configuration is via `.env`. See [.env.example](./.env.example) for the
full set. These must be changed before deploying:

- `SERVICE_TOKEN` — shared secret for internal service-to-service auth.
- `JWT_SECRET` — HMAC key used by `auth-mcp` to sign user access tokens.

Optional Phase-2 integrations:
- `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_ENGINE_ID` — enable real Google Custom
  Search lookups in the websearch MCP. Without these, the service falls back
  to heuristic-only scoring (WHOIS + domain rules).
- `SMTP_HOST` (+ user/password) — send real email notifications. Without it,
  the notification MCP logs emails to stdout (useful for dev).
- `BOOTSTRAP_ADMIN_EMAIL` + `BOOTSTRAP_ADMIN_PASSWORD` — auto-create an admin
  user in `auth-mcp` on first start (idempotent).

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

Explainability uses `shap.TreeExplainer`; the API surfaces the top features
by absolute SHAP contribution with a human-readable label and direction
(fraud vs legit).

### OCR

`POST /api/v1/jobs/analyze-file` accepts PDF / PNG / JPG:
- PDFs are first parsed via PyMuPDF's text layer; if empty, each page is
  rasterized and run through Tesseract.
- Images go straight through Tesseract.
- Plain text is passed through unchanged.

### Re-training

```bash
# Inside the ml-engine container (or your local venv):
python -m app.models.train --data datasets/sample_jobs.csv --out model_store/
# Then reload the live model without restarting:
curl -X POST http://localhost:8100/model/reload
```

---

## Awareness module

Articles and quizzes are seeded into the database on first startup
([`mcp-servers/database/app/seed.py`](./mcp-servers/database/app/seed.py)).
Articles are stored as Markdown and rendered inside the React app via a
minimal, XSS-safe renderer ([`frontend/src/lib/markdown.tsx`](./frontend/src/lib/markdown.tsx)).
Quiz answers are kept server-side and never sent down to the client until
the user submits.

To add or edit content, modify `seed.py` and bump the file's modification
time, or POST directly to `db-mcp` `/articles` / `/quizzes` (service-token
required).

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
cd mcp-servers/filesystem && pip install -e ".[test]" && pytest -q
cd mcp-servers/websearch && pip install -e ".[test]" && pytest -q
cd mcp-servers/notification && pip install -e ".[test]" && pytest -q
cd mcp-servers/analytics && pip install -e ".[test]" && pytest -q
cd backend && pip install -e ".[test]" && pytest -q
cd frontend && npm install && npm test
```

Phase 2 totals: **84 Python tests + 4 TypeScript tests**, all passing.

### End-to-end smoke (docker-compose)

```bash
docker compose up -d --build
sleep 60
curl -fsS localhost:8000/api/v1/healthz | jq
curl -fsS localhost:5173 -o /dev/null -w "frontend: %{http_code}\n"

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
│   ├── PHASE1_PLAN.md
│   └── PHASE2_PLAN.md
├── frontend/                      # Vite + React + Tailwind + Recharts
│   ├── src/pages/                 # user + admin pages
│   ├── src/components/            # ScoreMeter, Layout, ExplanationsTable
│   ├── src/lib/                   # api client, markdown renderer, formatters
│   └── Dockerfile                 # multi-stage: node build → nginx static
├── backend/                       # FastAPI gateway
│   ├── app/api/                   # routers (auth, jobs, me, reports,
│   │                              # awareness, companies, files, admin,
│   │                              # internal)
│   ├── app/clients/               # downstream HTTP clients
│   └── app/ws/                    # WebSocket hub
├── ml-engine/                     # ML detection engine + OCR
│   ├── app/pipeline/              # feature extractors
│   ├── app/models/                # train + SHAP
│   ├── app/ocr/                   # PDF/image text extraction
│   └── datasets/                  # bundled training data + lexicon
├── mcp-servers/
│   ├── _common/                   # shared http + logging + security helpers
│   ├── auth/                      # JWT issuance + user CRUD + admin role
│   ├── database/                  # Postgres CRUD for jobs/predictions/
│   │                              # reports/articles/quizzes/notifications
│   ├── memory/                    # ChromaDB-backed RAG + user context
│   ├── filesystem/                # uploads + PDF report rendering
│   ├── websearch/                 # Google CSE + WHOIS company verification
│   ├── notification/              # email + WebSocket notifications
│   └── analytics/                 # aggregated metrics + dashboard composition
├── infra/
│   └── postgres/init.sql
└── tests/integration/             # docker-compose end-to-end
```

---

## License

Proprietary — internal use only unless otherwise stated.
