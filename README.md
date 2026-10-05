# Egyptora backend

FastAPI + PostgreSQL backend for Egyptora, the AI trip planner for Egypt.
Three front ends (traveler, company, admin) are vibe-coded from this API's OpenAPI spec at `/openapi.json`.

- **Full spec, ERD and the 6-person split:** see the team doc (ERD, features & endpoints + Backend split tabs).
- **How we work every day:** [CONTRIBUTING.md](CONTRIBUTING.md)

## Run it (first time)

```bash
git clone <repo-url> && cd egyptora-backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # Windows: copy .env.example .env
docker compose up -d db            # PostgreSQL 16 on localhost:5432 (+ egyptora_test for pytest)
alembic upgrade head               # creates all 21 tables + the hotel_best_price view
python -m scripts.seed             # sample users, companies, cities, interests
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs. Log in with `POST /api/v1/auth/login`
(`admin@egyptora.dev` / `egyptora123`), copy `access_token`, click **Authorize**.

Run the checks: `pytest` and `ruff check . && ruff format --check .`

## What already works

- All 21 tables + the view, as SQLAlchemy models and one Alembic migration.
- Login, register, refresh, `/me`, and `require_role(...)` for every route.
- All 97 endpoints exist with their path, inputs and a description of why they exist.
  Each one returns **501 Not implemented (owner: Person N)** until its owner builds it.
- Every AI piece in `app/ai/` returns sample data while `AI_MOCK=true`, so nobody waits for a model.

## Folder layout and owners

```
app/
  core/            config, database, security, deps (require_role, not_implemented)   Person 1
  main.py          registers every router                                              Person 1
  models.py        imports every model for Alembic                                     Person 1
  ai/
    sentiment.py   review sentiment                                                    Person 1
    planner.py     trip planner agent                                                  Person 2
    chat_agent.py  chat that edits the trip                                            Person 3
    recognizer.py  monument recognition                                                Person 4
    place_qa.py    "ask more" about a place                                            Person 4
    nl2sql.py      hotel question -> SQL                                               Person 5
  modules/
    accounts/      users, auth, /me                                         (T1)       Person 1
    companies/     companies, reviews, trust score, company + admin routes  (T9 C1 C2 C5 A2)  Person 1
    trips/         trips, days, items, totals, preferences lookups          (T2 T3 T4) Person 2
    chat/          chat messages, trip changes                              (T5)       Person 3
    sharing/       summary, save, share links                               (T10)      Person 3
    admin_stats/   admin overview                                           (A1)       Person 3
    catalog/       cities, interests                                        (A4 part)  Person 3
    places/        places, images, scans                                    (T6 A4 A5 part) Person 4
    hotels/        hotels, NL search                                        (T7 A3 part) Person 5
    ai_quality/    nl_queries, training examples                            (A5 part)  Person 5
    offers/        offers, price alerts, ranking, best-price view           (T8 C3 C4 A3 part) Person 6
migrations/versions/   one file per schema change (whoever changes their models.py)
scripts/seed.py        runs every module's seed.py in order
tests/test_pN_*.py     each person's tests
```

Inside each module: `models.py` (tables), `schemas.py` (request/response shapes),
`router*.py` (endpoints), `service.py` / helpers (logic), `seed.py` (sample data).
