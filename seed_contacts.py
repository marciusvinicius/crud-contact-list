import random
import string

import requests

API_BASE = "http://localhost:8000"


FIRST_NAMES = [
    "Alice",
    "Bob",
    "Carol",
    "David",
    "Eve",
    "Frank",
    "Grace",
    "Henry",
    "Ivy",
    "Jack",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Martinez",
    "Wilson",
]


def random_email(first: str, last: str, index: int) -> str:
    domain = random.choice(["example.com", "test.com", "mail.com"])
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return f"{first.lower()}.{last.lower()}{index}{suffix}@{domain}"


def make_contact(i: int) -> dict:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    email_count = random.randint(1, 3)
    emails = [random_email(first, last, idx) for idx in range(email_count)]
    return {
        "first_name": f"{first}{i}",
        "last_name": last,
        "emails": emails,
    }


def main(total: int = 1000) -> None:
    for i in range(total):
        contact = make_contact(i)
        resp = requests.post(f"{API_BASE}/contacts", json=contact)
        if resp.status_code not in (200, 201):
            print(f"Failed to create contact {i}: {resp.status_code} - {resp.text}")
        if (i + 1) % 100 == 0:
            print(f"Created {i + 1} contacts")

    print("Done seeding contacts.")


if __name__ == "__main__":
    main()

