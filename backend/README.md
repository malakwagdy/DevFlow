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

- `POST /auth/register`: `email`, `password`, `full_name`, optional `role` (default
  `application_developer`), optional `company_name`
  (creates the company with you as `owner` plus one `Default` team). Returns a token.
- `POST /auth/login`: returns a token.
- `POST /auth/verify-email`: `token` from the emailed link (sent on register). No login needed.
- `POST /auth/resend-verification`: needs a token; emails a new verification link.
- `POST /auth/forgot-password`: `email`. Always `202`, whether or not the account exists.
- `POST /auth/reset-password`: `token` from the emailed link, `new_password`. The link works once.
- `GET /auth/me`: needs `Authorization: Bearer <access_token>`.
- `GET /session`: same auth. Returns what the app shell shows: `user` (`name`, `initials`, `email`)
  and `workspace` (`slug`, `name`, `initials`, `cluster`), or `workspace: null` without a company.
  `slug` is generated from the company name; `cluster` is always `null` until deployments exist.

Emailed links open the frontend at `/verify-email?token=...` and `/reset-password?token=...`;
those pages POST the token to the endpoints above. With `EMAIL_BACKEND=console` (the default)
emails are printed to the API log instead of being sent.

## Account settings API (needs a token)

- `PATCH /users/me`: `full_name` and/or `email`. A new email needs `current_password`, becomes
  unverified and gets a verification link; the old address is notified.
- `POST /users/me/password`: `current_password`, `new_password`. Signs out every session and
  returns a fresh token.
- `DELETE /users/me`: body `{"password": ...}`. Deletes the account and its projects, revokes
  GitHub access, and deletes the company if you're its only member.

Changing or resetting the password invalidates every access token issued before it.

## Rate limits

Repeated attempts get `429` with a `Retry-After` header (seconds). Limits live in
`app/core/rate_limit.py`: login 20 per 5 min per IP, and 5 wrong passwords per 15 min per email
(the account is then locked for that window, even with the right password; a password reset
lifts it); register 10 per hour per IP; forgot-password 5 per 15 min per IP and 3 per hour per
email; resend-verification 3 per hour; 5 wrong current passwords per 15 min on settings.
Counters are in memory per process, so they reset on restart and each worker counts separately.

To protect an endpoint, add a `CurrentUserDep` parameter, or `Depends(require_roles(...))`,
both from `app/api/dependencies.py`.
