# DevFlow

DevSecOps platform for connecting GitHub repositories, selecting deployment templates, and deploying Dockerized apps through Jenkins pipelines with built-in security scanning.

## Local setup

    cp .env.example .env
    docker compose up -d postgres    # PostgreSQL 16; also creates devflow_test for pytest
    pip install -r requirements.txt
    alembic upgrade head             # create / update the schema
    uvicorn app.main:app --reload
    pytest

After changing a model in `app/models/`, run
`alembic revision --autogenerate -m "describe change"` and review the generated file.

Create the first platform admin (public registration can't):

    python -m scripts.create_admin --email admin@example.com --name "Admin"

## Health checks (no auth)

- `GET /health`: liveness, `200` while the process is running. Doesn't touch the database.
- `GET /health/ready`: readiness, `200` if PostgreSQL answers within 2 s, otherwise `503`.

## Auth API

- `POST /auth/register`: `email`, `password`, `full_name`, `role`, optional `company_name`
  (creates the company with you as `owner` plus one `Default` team). Returns a token.
- `POST /auth/login`: returns a token.
- `GET /auth/me`: needs `Authorization: Bearer <access_token>`.

To protect an endpoint, add a `CurrentUserDep` parameter, or `Depends(require_roles(...))`,
both from `app/api/dependencies.py`.
