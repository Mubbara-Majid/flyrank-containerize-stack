# FlyRank Backend Track — Containerized Task API with Auth

A FastAPI task management API backed by PostgreSQL, fully containerized with Docker, and secured with Supabase Auth. The whole stack — app, database, and authentication — starts with a single command.

This project has evolved through three FlyRank assignments in one continuous repo:

| Assignment | What it added |
|---|---|
| A1 | In-memory CRUD API |
| A2 | Swapped storage to SQLite |
| A3 | Containerized with Docker + swapped storage to Postgres |
| A4 (current) | Added Supabase authentication and protected routes |

The task endpoints and their behavior never changed across any of these — only the storage layer and, now, the access control around them did. Full history of each stage is in the git log, not repeated here.

## Architecture

- `main.py` — FastAPI routes only. Wires together the database and auth layers below.
- `repository.py` — the only file that talks to Postgres. Every SQL query lives here, parameterized (`%s` placeholders).
- `supabase_client.py` — initializes the Supabase client from environment variables.
- `auth.py` — every direct Supabase Auth call (sign up, sign in, verify token, sign out) lives here.
- `deps.py` — FastAPI dependency layer. `get_current_user` extracts and verifies a bearer token, reused across every protected route via `Depends(...)`.
- `Dockerfile` — builds the app into its own image.
- `compose.yaml` — defines two services, `api` and `db`, networked together.

## Why this stack

- **Postgres in Docker**: no local database install, no version conflicts — the official `postgres` image runs as a container with a volume for persistence.
- **One command starts everything**: `docker compose up` brings up the app and database together.
- **Supabase Auth as the identity provider**: passwords are never stored or hashed by this code. Supabase handles accounts and issues signed JWTs; this API's job is only to verify tokens and guard routes — the correct division of responsibility for a backend that doesn't want to own password security.

## Environment variables

Copy `.env.example` to `.env` before running locally (outside Docker Compose):

```bash
cp .env.example .env
```

```
DATABASE_URL=postgres://postgres:dev@localhost:5432/tasks
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```

`.env` is git-ignored and never committed. Use only the **anon** key from your Supabase project — never the `service_role` key, which bypasses all security and must stay server-side and secret in a real deployment.

Inside `docker compose`, the `api` service gets `DATABASE_URL` directly from `compose.yaml`, pointing at the `db` service by name instead of `localhost`.

## How to run it

**With Docker Compose (recommended — starts app + database together):**

```bash
docker compose up --build
```

The API runs at `http://localhost:8000`. Interactive docs (Swagger UI) are at `http://localhost:8000/docs`. On first run, the `tasks` table is created and seeded with three example tasks automatically.

**Locally without Compose (for development):**

```bash
docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks -p 5432:5432 -v taskdata:/var/lib/postgresql -d postgres
cp .env.example .env
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
uvicorn main:app --reload
```

## Endpoints

| Method | Path | Description | Auth required |
|---|---|---|---|
| GET | `/tasks` | List all tasks | No |
| GET | `/tasks/{id}` | Get a single task | No |
| POST | `/tasks` | Create a task | No |
| PUT | `/tasks/{id}` | Update a task | No |
| DELETE | `/tasks/{id}` | Delete a task | No |
| POST | `/auth/signup` | Create a new user account | No |
| POST | `/auth/login` | Authenticate and receive a JWT | No |
| POST | `/auth/logout` | End the user's session | Yes |
| GET | `/protected/profile` | Read the current user's private profile | Yes |
| GET | `/protected/dashboard` | Second protected route reusing the same guard | Yes |
| GET | `/public/info` | Open, unauthenticated info | No |

Status codes: `200` / `201` / `204` on success, `400` invalid body, `401` missing/invalid/expired token, `404` unknown task id.

## Authentication flow

1. `POST /auth/signup` — create an account with an email and password. Supabase stores and hashes the password; this API never sees or stores it.
2. `POST /auth/login` — exchange credentials for a JWT (`access_token` + `refresh_token`).
3. Send the access token on every protected request: `Authorization: Bearer <token>`.
4. The server verifies the token against Supabase on each request via `supabase.auth.get_user(token)` — a real network call, not just decoding the token locally. A tampered or expired token is rejected with `401`.
5. `POST /auth/logout` revokes the current session.

The verification logic lives in one place (`deps.py`'s `get_current_user`), applied to every protected route via FastAPI's `Depends(...)` — no auth logic is duplicated per route.

## Try it in Swagger UI

Visit `http://localhost:8000/docs`. Protected routes show a lock icon. Click **Authorize**, paste an access token from `/auth/login`, and use **Try it out** on any protected route directly from the browser.

![Screenshot showing protected routes](screenshots/ss-swagger.png)

## Proof the API didn't change across storage engines

The same request/response shapes and status codes that worked against the in-memory version (A1) and the SQLite version (A2) work identically against Postgres (A3). Adding authentication (A4) didn't touch the task routes' internal logic either — it added new routes and a guard, without altering how `/tasks` behaves for an already-open route. Separating routes from storage and access control is what makes each of these swaps a one-file change instead of a rewrite.

## Persistence proof

1. **App restart** — created tasks, restarted the server, confirmed the seed never duplicated.
2. **Full stack restart** — created a task, ran `docker compose down` (destroying both containers), then `docker compose up`. The task was still present, and Postgres logs showed `"PostgreSQL Database directory appears to contain a database; Skipping initialization"` — confirming the named volume, not the container, is what keeps the data alive.
