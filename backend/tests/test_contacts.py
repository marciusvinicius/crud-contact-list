import os
import sqlite3
from typing import Generator

import pytest
from fastapi.testclient import TestClient

import backend
import backend.database as db


TEST_DB_PATH = "test_contacts.db"


def setup_module(module):
  # Point database layer at a test database and initialise schema
  db.DB_PATH = TEST_DB_PATH
  if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
  db.init_db()


def teardown_module(module):
  if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)


def clear_db():
  conn = sqlite3.connect(TEST_DB_PATH)
  try:
    conn.execute("DELETE FROM emails")
    conn.execute("DELETE FROM contacts")
    conn.commit()
  finally:
    conn.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
  clear_db()
  with TestClient(backend.app) as c:
    yield c


def test_create_and_get_contact(client: TestClient):
  payload = {
    "first_name": "John",
    "last_name": "Doe",
    "emails": ["john.doe@example.com"],
  }

  resp = client.post("/contacts", json=payload)
  assert resp.status_code == 201
  created = resp.json()
  assert created["id"] is not None
  assert created["first_name"] == "John"
  assert created["last_name"] == "Doe"
  assert created["emails"] == ["john.doe@example.com"]

  contact_id = created["id"]

  resp_get = client.get(f"/contacts/{contact_id}")
  assert resp_get.status_code == 200
  fetched = resp_get.json()
  assert fetched == created


def test_update_contact_and_emails(client: TestClient):
  payload = {
    "first_name": "Alice",
    "last_name": "Smith",
    "emails": ["alice@example.com", "alice.work@example.com"],
  }
  resp = client.post("/contacts", json=payload)
  contact_id = resp.json()["id"]

  update_payload = {
    "first_name": "Alicia",
    "emails": ["alicia@example.com"],
  }

  resp_update = client.put(f"/contacts/{contact_id}", json=update_payload)
  assert resp_update.status_code == 200
  updated = resp_update.json()
  assert updated["first_name"] == "Alicia"
  assert updated["last_name"] == "Smith"
  assert updated["emails"] == ["alicia@example.com"]


def test_delete_contact(client: TestClient):
  payload = {
    "first_name": "Bob",
    "last_name": "Brown",
    "emails": ["bob@example.com"],
  }
  resp = client.post("/contacts", json=payload)
  contact_id = resp.json()["id"]

  resp_delete = client.delete(f"/contacts/{contact_id}")
  assert resp_delete.status_code == 204

  resp_get = client.get(f"/contacts/{contact_id}")
  assert resp_get.status_code == 404


def test_search_contacts_by_name_and_email(client: TestClient):
  contacts = [
    {"first_name": "Carol", "last_name": "Jones", "emails": ["carol@example.com"]},
    {"first_name": "David", "last_name": "Miller", "emails": ["david@work.com"]},
    {"first_name": "Eve", "last_name": "Smith", "emails": ["eve.personal@mail.com"]},
  ]
  for c in contacts:
    client.post("/contacts", json=c)

  resp_name = client.get("/contacts", params={"q": "carol"})
  assert resp_name.status_code == 200
  results_name = resp_name.json()
  assert len(results_name) == 1
  assert results_name[0]["first_name"] == "Carol"

  resp_email = client.get("/contacts", params={"q": "work.com"})
  assert resp_email.status_code == 200
  results_email = resp_email.json()
  assert len(results_email) == 1
  assert results_email[0]["first_name"] == "David"


def test_reject_empty_first_or_last_name_on_create(client: TestClient):
  payload = {
    "first_name": " ",
    "last_name": "Doe",
    "emails": ["john.doe@example.com"],
  }
  resp = client.post("/contacts", json=payload)
  assert resp.status_code == 422
  assert "first_name must not be empty" in resp.json()["detail"]

  payload = {
    "first_name": "John",
    "last_name": "   ",
    "emails": ["john.doe@example.com"],
  }
  resp = client.post("/contacts", json=payload)
  assert resp.status_code == 422
  assert "last_name must not be empty" in resp.json()["detail"]


def test_reject_empty_email_list_on_create(client: TestClient):
  payload = {
    "first_name": "John",
    "last_name": "Doe",
    "emails": [],
  }
  resp = client.post("/contacts", json=payload)
  assert resp.status_code == 422
  # exact error message may come from Pydantic or our own normalization;
  # we only require that the request is rejected.


def test_trim_names_and_emails_on_create(client: TestClient):
  payload = {
    "first_name": "  John  ",
    "last_name": "  Doe ",
    "emails": ["  john.doe@example.com  "],
  }
  resp = client.post("/contacts", json=payload)
  assert resp.status_code == 201
  created = resp.json()
  assert created["first_name"] == "John"
  assert created["last_name"] == "Doe"
  assert created["emails"] == ["john.doe@example.com"]


def test_validation_on_update_contact(client: TestClient):
  # create base contact
  payload = {
    "first_name": "Jane",
    "last_name": "Doe",
    "emails": ["jane@example.com"],
  }
  resp = client.post("/contacts", json=payload)
  assert resp.status_code == 201
  contact_id = resp.json()["id"]

  # empty first_name should be rejected
  update_payload = {"first_name": "   "}
  resp_update = client.put(f"/contacts/{contact_id}", json=update_payload)
  assert resp_update.status_code == 422
  assert "first_name must not be empty" in resp_update.json()["detail"]

  # empty emails list should be rejected
  update_payload = {"emails": []}
  resp_update = client.put(f"/contacts/{contact_id}", json=update_payload)
  assert resp_update.status_code == 422
  assert "At least one valid email is required" in resp_update.json()["detail"]


def test_pagination_limit_and_offset(client: TestClient):
  # create 12 contacts so we can paginate
  for i in range(12):
    payload = {
      "first_name": f"User{i}",
      "last_name": "Paginated",
      "emails": [f"user{i}@example.com"],
    }
    resp = client.post("/contacts", json=payload)
    assert resp.status_code == 201

  # first page
  resp_page1 = client.get("/contacts", params={"limit": 5, "offset": 0})
  assert resp_page1.status_code == 200
  page1 = resp_page1.json()
  assert len(page1) == 5

  # second page
  resp_page2 = client.get("/contacts", params={"limit": 5, "offset": 5})
  assert resp_page2.status_code == 200
  page2 = resp_page2.json()
  assert len(page2) == 5

  # ensure no overlap between first two pages
  ids_page1 = {c["id"] for c in page1}
  ids_page2 = {c["id"] for c in page2}
  assert ids_page1.isdisjoint(ids_page2)

  # third page (should contain the remaining 2)
  resp_page3 = client.get("/contacts", params={"limit": 5, "offset": 10})
  assert resp_page3.status_code == 200
  page3 = resp_page3.json()
  assert len(page3) == 2


def test_csv_export_for_selected_contacts(client: TestClient):
  # create two contacts
  payload1 = {
    "first_name": "Csv",
    "last_name": "One",
    "emails": ["one@example.com", "other1@example.com"],
  }
  payload2 = {
    "first_name": "Csv",
    "last_name": "Two",
    "emails": ["two@example.com"],
  }

  resp1 = client.post("/contacts", json=payload1)
  resp2 = client.post("/contacts", json=payload2)
  assert resp1.status_code == 201
  assert resp2.status_code == 201
  id1 = resp1.json()["id"]
  id2 = resp2.json()["id"]

  resp_csv = client.get("/contacts-export", params=[("ids", id1), ("ids", id2)])
  assert resp_csv.status_code == 200
  assert resp_csv.headers.get("content-type", "").startswith("text/csv")

  body = resp_csv.text
  # CSV header + 2 rows
  lines = [line for line in body.strip().splitlines() if line]
  assert len(lines) == 3
  assert lines[0].startswith("id,first_name,last_name,emails")
  # ensure both contact IDs are present somewhere in the CSV
  assert any(str(id1) in line for line in lines[1:])
  assert any(str(id2) in line for line in lines[1:])


def test_pagination_respected_with_search(client: TestClient):
  # create contacts that will all match the same search term
  for i in range(12):
    payload = {
      "first_name": f"SearchUser{i}",
      "last_name": "SearchScope",
      "emails": [f"search{i}@example.com"],
    }
    resp = client.post("/contacts", json=payload)
    assert resp.status_code == 201

  # first page of search results
  resp_page1 = client.get("/contacts", params={"q": "searchscope", "limit": 5, "offset": 0})
  assert resp_page1.status_code == 200
  page1 = resp_page1.json()
  assert len(page1) == 5

  # second page of search results
  resp_page2 = client.get("/contacts", params={"q": "searchscope", "limit": 5, "offset": 5})
  assert resp_page2.status_code == 200
  page2 = resp_page2.json()
  assert len(page2) == 5

  ids_page1 = {c["id"] for c in page1}
  ids_page2 = {c["id"] for c in page2}
  assert ids_page1.isdisjoint(ids_page2)

  # third page should contain remaining 2 results
  resp_page3 = client.get("/contacts", params={"q": "searchscope", "limit": 5, "offset": 10})
  assert resp_page3.status_code == 200
  page3 = resp_page3.json()
  assert len(page3) == 2


