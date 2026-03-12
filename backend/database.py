import sqlite3
from typing import List

from .schemas import Contact

DB_PATH = "contacts.db"


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
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_first_name ON contacts(first_name);"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_last_name ON contacts(last_name);"
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_emails_email ON emails(email);")
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
    from fastapi import HTTPException

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

