## Contacts CRUD (FastAPI + Vanilla JS)

### Backend

- **Run API**:

```bash
pip install -r requirements.txt
uvicorn backend:app --reload
```

The API listens on `http://localhost:8000`.

#### Seed with sample data

With the API running, you can create 1000 random contacts to test the UI:

```bash
python seed_contacts.py
```

This uses the `/contacts` endpoint and fills the in-memory store (data resets when you restart the API).

### Frontend

- **Open UI**:
  - The simplest option is to use a static file server from this directory, for example:

```bash
python -m http.server 5500
```

  - Then open `http://localhost:5500/index.html` in your browser.

The UI calls the FastAPI backend at `http://localhost:8000` and provides:

- **Left side panel**: list of contacts, title "Contacts" and a blue **+** button to start a new contact.
- **Middle**: first and last name inputs, list of emails where each row shows a red **Delete** button on hover, plus a `+ Add email` button at the end of the list.

