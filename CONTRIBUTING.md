# Contributing

## Workflow

1. Branch from an up-to-date `main`: `git switch -c <area>/<short-description>`.
2. Keep pull requests small and focused, ideally one endpoint or one fix.
3. Before pushing, run:
   ```bash
   ruff check . --fix && ruff format .
   pytest
   ```
4. Open a pull request into `main`. It can be merged once the CI check passes.
   Use **Squash and merge**.

`main` is protected. All changes go through pull requests.

## Database changes

Change the SQLAlchemy model, then generate and review a migration:

```bash
alembic revision --autogenerate -m "short description"
alembic upgrade head
```

If two migrations end up with the same parent, run `alembic merge heads -m "merge"` and commit the result.

## Conventions

- Each module under `app/modules/` owns its models, schemas, routes and seed data.
- Every endpoint declares a `response_model` and includes a docstring describing its purpose.
- AI functions in `app/ai/` keep the same inputs and outputs in mock and real mode.
- Adding or removing an endpoint? Update the count in `tests/test_smoke.py`.
- Never commit secrets, `.env`, model weights or uploaded files.
