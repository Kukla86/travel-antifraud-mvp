#!/bin/sh
. ../.venv/bin/activate
exec uvicorn app.main_simple:app --reload --host 0.0.0.0 --port 8000
