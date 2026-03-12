#!/bin/sh
set -e

uvicorn backend:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Give the server a moment to start before seeding
sleep 5

python seed_contacts.py || echo "Seeding contacts failed (continuing without seed)."

wait "$UVICORN_PID"

