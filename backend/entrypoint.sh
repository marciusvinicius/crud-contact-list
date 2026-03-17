#!/bin/sh
set -e

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
UVICORN_PID=$!

# Give the server a moment to start before seeding
sleep 5

python -m backend.seed_contacts || echo "Seeding contacts failed (continuing without seed)."

wait "$UVICORN_PID"

