import os
import sqlite3
from typing import Generator

import pytest
from fastapi.testclient import TestClient

import backend


TEST_DB_PATH = "test_contacts.db"


def setup_module(module):
  # Point backend at a test database and initialise schema
  backend.DB_PATH = TEST_DB_PATH
  if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
  backend.init_db()


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

