# Phase 2 — Implementation Plan

Phase 2 builds on the Phase-1 backbone (gateway, ML engine, memory/auth/db
MCPs) to deliver the full feature set described in `docs/ARCHITECTURE.md`.

## Scope

1. **Frontend** (`frontend/`) — Vite + React + TypeScript + Tailwind +
   Framer Motion + Recharts, served behind nginx in production.
2. **Filesystem MCP** (`mcp-servers/filesystem/`) — content-addressed uploads,
   PDF report generation via ReportLab, service-token gated.
3. **Web-search MCP** (`mcp-servers/websearch/`) — company legitimacy
   verification via Google Custom Search + WHOIS; heuristic sigmoid scoring.
4. **Notification MCP** (`mcp-servers/notification/`) — email (SMTP-or-console)
   + WebSocket fan-out via the backend.
5. **Analytics MCP** (`mcp-servers/analytics/`) — TTL-cached composition of
   summary / fraud-over-time / top-features dashboards.
6. **Backend gateway extensions** — new routers for reports, awareness,
   company verification, files, admin, and an internal WebSocket push
   endpoint.
7. **Database MCP extensions** — `scam_reports`, `articles`, `quizzes`,
   `quiz_attempts`, `company_verifications`, `analytics_events`,
   `notifications` tables; idempotent seed of articles + quizzes on startup.
8. **Auth MCP extensions** — admin role + idempotent admin bootstrap from
   env.
9. **Awareness module** — 3 seeded articles + 1 seeded quiz with 5 questions.
10. **Admin dashboard** — Recharts KPIs + scam report review workflow.

## Out of scope (deferred)

- Production deployment, scaling, autoscaling.
- Prometheus / Grafana observability.
- mTLS between internal services (still on `X-Service-Token`).
- OAuth / SSO providers.
- Real labelled dataset (still using synthetic 1000-row sample).
- Custom code-splitting for the Vite bundle.

## Architecture deltas vs Phase 1

```
                                ┌───────────────┐
                                │   Frontend    │  :5173 → :80 (nginx)
                                └───────┬───────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │ Backend gateway  │ :8000
                              └─────────┬────────┘
                                        │
   ┌────────────┬────────────┬──────────┼──────────┬────────────┬────────────┐
   ▼            ▼            ▼          ▼          ▼            ▼            ▼
auth-mcp    db-mcp       memory-    ml-engine  filesystem-  websearch-   analytics-
 :8700       :8500         mcp        :8100       mcp          mcp          mcp
                          :8200                  :8400         :8600        :8800
                                                                              │
                                                                              ▼
                                                                       notification-mcp
                                                                            :8300
```

All inter-service traffic is gated by `X-Service-Token`. Only `backend:8000`
and `frontend:5173` are published on the host.

## Tests added

| Service / area      | Tests | Notes                                              |
|---------------------|-------|----------------------------------------------------|
| backend gateway     | +10   | reports, awareness, companies, admin, internal WS |
| db-mcp              | +12   | CRUD for new entities + edge cases                 |
| filesystem-mcp      | +5    | upload+retrieve, PDF generation, auth              |
| websearch-mcp       | +4    | fallback path, mocked CSE+WHOIS                    |
| notification-mcp    | +4    | email console mode, WS push, auth                  |
| analytics-mcp       | +4    | dashboard composition, cache, auth                 |
| frontend            | +4    | format helpers + markdown renderer XSS safety      |

Totals: **84 Python + 4 TypeScript tests**, all passing.

## Files written

See the diff against `phase-1`. Major directories added:

```
frontend/                      # complete Vite app
mcp-servers/filesystem/        # complete service
mcp-servers/websearch/         # complete service
mcp-servers/notification/      # complete service
mcp-servers/analytics/         # complete service
backend/app/api/{admin,awareness,companies,files,internal,reports}.py
backend/app/clients/{analytics,filesystem,notification,websearch}.py
mcp-servers/auth/app/seed.py
mcp-servers/database/app/seed.py
mcp-servers/database/tests/test_phase2.py
backend/tests/test_phase2.py
docs/PHASE2_PLAN.md            # (this file)
```

## Risks / known follow-ups

- Vite bundle is ~742 KB before gzip; consider route-level code splitting if
  it grows further.
- The websearch MCP's heuristic scoring is intentionally conservative when
  CSE credentials are absent; users should provide `GOOGLE_CSE_API_KEY` for
  meaningful results.
- The notification MCP currently logs emails to stdout when `SMTP_HOST` is
  unset — fine for development, swap to a real provider before production.
- Quiz answers are kept in the DB and never leak to the public API
  (`schemas/awareness.py:QuizPublic` strips `correct_index` and
  `explanation`).
