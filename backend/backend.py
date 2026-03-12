from typing import List, Optional

import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr


DB_PATH = "contacts.db"


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    emails: List[EmailStr]


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    emails: Optional[List[EmailStr]] = None


class Contact(ContactBase):
    id: int


app = FastAPI(title="Contacts API")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
            );
            """
        )
        # Indexes
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_first_name ON contacts(first_name);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_last_name ON contacts(last_name);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_emails_email ON emails(email);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_emails_contact_id ON emails(contact_id);"
        )
        conn.commit()
    finally:
        conn.close()


def row_to_contact(conn: sqlite3.Connection, row: sqlite3.Row) -> Contact:
    email_rows = conn.execute(
        "SELECT email FROM emails WHERE contact_id = ? ORDER BY id ASC",
        (row["id"],),
    ).fetchall()
    emails = [r["email"] for r in email_rows]
    return Contact(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        emails=emails,
    )


def get_contact_or_404(contact_id: int) -> Contact:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, first_name, last_name FROM contacts WHERE id = ?",
            (contact_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Contact not found")
        return row_to_contact(conn, row)
    finally:
        conn.close()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# CORS configuration
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/contacts", response_model=List[Contact])
def list_contacts(q: Optional[str] = Query(default=None)) -> List[Contact]:
    conn = get_connection()
    try:
        if q:
            q_like = f"%{q.lower()}%"
            rows = conn.execute(
                """
                SELECT DISTINCT c.id, c.first_name, c.last_name
                FROM contacts c
                LEFT JOIN emails e ON e.contact_id = c.id
                WHERE lower(c.first_name) LIKE ?
                   OR lower(c.last_name) LIKE ?
                   OR lower(e.email) LIKE ?
                ORDER BY c.last_name, c.first_name, c.id
                """,
                (q_like, q_like, q_like),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, first_name, last_name FROM contacts ORDER BY last_name, first_name, id"
            ).fetchall()

        return [row_to_contact(conn, row) for row in rows]
    finally:
        conn.close()


@app.post("/contacts", response_model=Contact, status_code=201)
def create_contact(contact_in: ContactCreate) -> Contact:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO contacts (first_name, last_name) VALUES (?, ?)",
            (contact_in.first_name, contact_in.last_name),
        )
        contact_id = cur.lastrowid
        for email in contact_in.emails:
            cur.execute(
                "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
                (contact_id, email),
            )
        conn.commit()

        row = conn.execute(
            "SELECT id, first_name, last_name FROM contacts WHERE id = ?",
            (contact_id,),
        ).fetchone()
        return row_to_contact(conn, row)
    finally:
        conn.close()


@app.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: int) -> Contact:
    return get_contact_or_404(contact_id)


@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: int, contact_update: ContactUpdate) -> Contact:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, first_name, last_name FROM contacts WHERE id = ?",
            (contact_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Contact not found")

        data = contact_update.dict(exclude_unset=True)

        first_name = data.get("first_name", row["first_name"])
        last_name = data.get("last_name", row["last_name"])

        conn.execute(
            "UPDATE contacts SET first_name = ?, last_name = ? WHERE id = ?",
            (first_name, last_name, contact_id),
        )

        if "emails" in data:
            conn.execute("DELETE FROM emails WHERE contact_id = ?", (contact_id,))
            for email in data["emails"] or []:
                conn.execute(
                    "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
                    (contact_id, email),
                )

        conn.commit()

        row = conn.execute(
            "SELECT id, first_name, last_name FROM contacts WHERE id = ?",
            (contact_id,),
        ).fetchone()
        return row_to_contact(conn, row)
    finally:
        conn.close()


@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM contacts WHERE id = ?",
            (contact_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Contact not found")

        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        return None
    finally:
        conn.close()


@app.get("/")
def root():
    return {"message": "Contacts API is running"}

