# How we work

Six people, one repo, `main` always works. Read this once, then follow the daily routine.

## Day 1 (first time only)

1. Install **Python 3.11+**, **Git**, **Docker Desktop** (or PostgreSQL 16 locally) and your editor (VS Code / Cursor).
2. Accept the GitHub invite and clone the repo.
3. Follow **Run it (first time)** in the README until http://localhost:8000/docs opens and `pytest` is green.
4. Find your files in the README's folder layout. Read the docstrings in your routers:
   each endpoint says **Why** it exists and **Then** what it unlocks.
5. Make your first branch and first PR: your module's `seed.py` with real sample data.
   Persons 1 and 3 already have seed data: Person 1 starts with `POST /company/register`, Person 3 with `GET /admin/stats`.

## Every day

**Start (10 min)**

```bash
git switch main && git pull
git switch -c p2/trips-generate        # new branch: p<your number>/<short-task>
# or continue yesterday's branch:  git switch p2/trips-generate && git rebase main
pip install -r requirements-dev.txt    # only if requirements changed
alembic upgrade head                   # get everyone's new migrations
```

Post one line in the team group: **Today: P2 #4 POST /trips/generate**.

**Build (one endpoint at a time, in your list's order)**

1. Replace `raise not_implemented(OWNER)` with the real code.
2. Add a `response_model` so the front end knows the exact shape.
3. Need a new column? Change **only your own** `models.py`, then:
   ```bash
   alembic revision --autogenerate -m "p2: add trip notes"
   # open the new file in migrations/versions/ and check it
   alembic upgrade head
   ```
4. Add at least one test in `tests/test_p<N>_*.py`.
5. Try it in `/docs` with **Authorize**.

**Finish (15 min)**

```bash
ruff check . --fix && ruff format .
pytest
git add -A && git commit -m "p2: POST /trips/generate saves days and items"
git push -u origin HEAD
```

Open a pull request into `main` and fill the template. No review is required:
once the CI check is green, merge it yourself with **Squash and merge**.

Post one line: **Done: P2 #4 · Next: #5 · Blocked: waiting for P6 best_offers_for_cities()**.

## Rules

- Never push to `main` directly. Every change goes through a PR, so CI checks it before it lands.
- Only edit your own files. Need a change in someone else's? Ask them, or open an issue and tag them.
- Shared files (`app/core/`, `app/main.py`, `app/models.py`, `migrations/env.py`): tell Person 1 before changing them.
- Small PRs: one endpoint (or 2-3 small ones) per PR.
- Two migrations with the same parent after pulling? Run `alembic merge heads -m "merge"` and commit it.
- Added or removed an endpoint? Update the count in `tests/test_smoke.py`.
- Never commit `.env`, API keys, model weights or uploaded photos.
- Keep `AI_MOCK=true` until your model is ready. The API shape of your AI function must not change when you switch it off.
- Calling another person's function (`recalculate_total`, `best_offers_for_cities`, `pause_all_for_company`)?
  Agree on its inputs and outputs in the group before either of you builds it.
