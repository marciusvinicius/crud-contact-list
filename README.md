## Contacts CRUD (FastAPI + Vanilla JS)

### Backend

- **Run API**:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Using Docker:

```bash
docker compose up --build
```

The API listens on `http://localhost:8000`.

- **Live API**:
  [Live API](https://crud-contact-list-2.onrender.com/)

#### Seed with sample data

With the API running, you can create 1000 random contacts to test the UI:

```bash
python seed_contacts.py
```

This uses the `/contacts` endpoint and fills the database.

### Frontend

- **Open UI**:
  - The simplest option is to use a static file server from this directory
  - Using docker compose:
    - docker compose up --build 

The UI calls the FastAPI backend at `http://localhost:8000`:

- **Live UI**:
- [LiveUI](https://crud-contact-list-ui.onrender.com/)

### Architecture overview

- **Backend**:
  - FastAPI application in the `backend` package.
  - `main.py`: application setup (CORS, startup, route registration).
  - `schemas.py`: Pydantic models for request/response validation.
  - `database.py`: SQLite connection, schema creation, and helpers.
  - `routes_contacts.py`: all contact CRUD + search + CSV export endpoints.
  - `seed_contacts.py`: seeds 1000 random contacts through the API.
- **Frontend**:
  - Vanilla JS + HTML + CSS in `front/`.
  - `index.html`: layout with contacts list, form, and actions.
  - `main.js`: all UI behavior, keyboard shortcuts, validation, pagination, and export.
  - `styles.css`: modern UI styling.
  - Optional Nginx container to serve the static frontend.

### Data model

- `contacts` table:
  - `id` (INTEGER, PK, autoincrement)
  - `first_name` (TEXT, required)
  - `last_name` (TEXT, required)
- `emails` table:
  - `id` (INTEGER, PK, autoincrement)
  - `contact_id` (INTEGER, FK → `contacts.id`, `ON DELETE CASCADE`)
  - `email` (TEXT, required)
- A contact is returned as:
  - `id`, `first_name`, `last_name`, `emails: List[str]` (all emails for that contact).

### Why FastAPI + SQLite

- **FastAPI**:
  - Simple, declarative route definitions and validation with Pydantic.
  - Automatic OpenAPI schema and JSON serialization that fit a small CRUD service well.
  - Easy to extend with middleware (CORS) and additional routers as the app grows.
- **SQLite**:
  - Zero external dependency: great for demos, local dev, and small deployments.
  - Supports foreign keys and indexes, which is enough for a single-node contacts app.
  - Stores everything in a single `contacts.db` file, making the app easy to run inside Docker.

### Possible future improvements

- Add authentication and per-user contact ownership.
- Introduce proper migrations (e.g. Alembic) instead of ad‑hoc `CREATE TABLE IF NOT EXISTS`.
- Replace SQLite with a networked database (PostgreSQL) for higher concurrency and scale.
- Add more fields (phone numbers, notes, tags) and richer search/filtering.
- Add backend rate limiting and better error payloads (error codes, fields) for API clients.
- Add github workflow to deploy on Render only after run all tests.
- Add more mobile-friendly interface
- Make clear when contacts that are outside of the pagination offset are part of the contact selections
