# FlyRank Backend Track — Week 1, Assignment A3
## Containerize your stack

A FastAPI task management API running against a real PostgreSQL database, both containerized with Docker. The whole stack — app and database — starts with a single command.

This is the third storage swap on this API: in-memory (A1) → SQLite (A2) → containerized Postgres (this one). The endpoints and their behavior never changed across any of the three; only the storage layer underneath did.

## Why Docker + Postgres

- **No local install required.** Postgres runs as a container from the official `postgres` image — nothing installed directly on the host machine, no version conflicts, no "works on my machine."
- **One command starts everything.** `docker compose up` brings up both the app and the database together, networked so they can talk to each other.
- **Real infrastructure, not a toy.** Postgres is the same engine behind a large share of production backends — this is the realistic version of what running a backend service actually looks like.

## Architecture

- `main.py` — FastAPI routes. Unchanged in shape from the A2 SQLite version — same paths, same status codes, same request/response shapes.
- `repository.py` — the only file that talks to the database. Every SQL query lives here, using parameterized (`%s`) placeholders. Swapping storage engines only ever touches this file.
- `Dockerfile` — builds the app into its own image.
- `compose.yaml` — defines two services, `api` and `db`, and networks them together.

## Environment variables

Copy `.env.example` to `.env` before running locally (outside Docker Compose):

```bash
cp .env.example .env
```

```
DATABASE_URL=postgres://postgres:dev@localhost:5432/tasks
```

`.env` is git-ignored — it never gets committed. Inside `docker compose`, the `api` service gets its own `DATABASE_URL` directly from `compose.yaml`, pointing at the `db` service by name instead of `localhost` (containers on the same compose network reach each other by service name).

## How to run it

**With Docker Compose (recommended — starts the whole stack):**

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. Postgres is available at `localhost:5432`. On first run, the `tasks` table is created and seeded with three example tasks automatically.

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

| Method | Path          | Description       |
|--------|---------------|--------------------|
| GET    | `/tasks`      | List all tasks     |
| GET    | `/tasks/{id}` | Get a single task  |
| POST   | `/tasks`      | Create a task      |
| PUT    | `/tasks/{id}` | Update a task      |
| DELETE | `/tasks/{id}` | Delete a task      |

Status codes: `200` / `201` / `204` on success, `400` for an invalid body, `404` for an unknown id.

## Example request

```bash
curl -i http://localhost:8000/tasks
```

```
HTTP/1.1 200 OK
content-type: application/json

[{"id":1,"title":"Buy milk","done":false},{"id":2,"title":"Walk the dog","done":true},{"id":3,"title":"Finish FlyRank assignment","done":false}]
```

## Proof the API didn't change across three storage engines

The same request/response shapes and status codes that worked against the in-memory version (A1) and the SQLite version (A2) work identically here against Postgres. That's the actual point of separating routes from storage: the API is a stable promise to its clients, and the database underneath is an implementation detail. Identical behavior across three completely different storage engines is the proof.

## Persistence proof

Two restarts were tested:

1. **App restart** — created tasks, restarted `uvicorn` several times, confirmed the seed never duplicated and created tasks were still present.
2. **Full stack restart** — created a task via `POST /tasks`, ran `docker compose down` (destroying both containers), then `docker compose up` again. The task was still present in `GET /tasks`, and the Postgres logs showed `"PostgreSQL Database directory appears to contain a database; Skipping initialization"` — confirming the named volume, not the container, is what kept the data alive.