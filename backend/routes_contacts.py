from typing import List, Optional

import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from .schemas import Contact, ContactCreate, ContactUpdate
from .database import get_connection, row_to_contact, get_contact_or_404


router = APIRouter()


@router.get("/contacts", response_model=List[Contact])
def list_contacts(
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[Contact]:
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
                LIMIT ? OFFSET ?
                """,
                (q_like, q_like, q_like, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, first_name, last_name
                FROM contacts
                ORDER BY last_name, first_name, id
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        return [row_to_contact(conn, row) for row in rows]
    finally:
        conn.close()


@router.post("/contacts", response_model=Contact, status_code=201)
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


@router.get("/contacts/{contact_id}", response_model=Contact)
def get_contact(contact_id: int) -> Contact:
    return get_contact_or_404(contact_id)


@router.put("/contacts/{contact_id}", response_model=Contact)
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


@router.delete("/contacts/{contact_id}", status_code=204)
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


@router.get("/contacts-export")
def export_contacts(ids: List[int] = Query(...)) -> StreamingResponse:
    if not ids:
        raise HTTPException(status_code=400, detail="No contact ids provided")

    conn = get_connection()
    try:
        placeholders = ",".join("?" for _ in ids)
        rows = conn.execute(
            f"""
            SELECT id, first_name, last_name
            FROM contacts
            WHERE id IN ({placeholders})
            ORDER BY last_name, first_name, id
            """,
            ids,
        ).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "first_name", "last_name", "emails"])

        for row in rows:
            contact = row_to_contact(conn, row)
            writer.writerow(
                [
                    contact.id,
                    contact.first_name,
                    contact.last_name,
                    ";".join(contact.emails),
                ]
            )

        output.seek(0)
        headers = {"Content-Disposition": 'attachment; filename="contacts.csv"'}
        return StreamingResponse(output, media_type="text/csv", headers=headers)
    finally:
        conn.close()

