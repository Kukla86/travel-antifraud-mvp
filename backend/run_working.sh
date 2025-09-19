#!/bin/sh
. ../.venv/bin/activate
exec uvicorn app.main_working:app --reload --host 0.0.0.0 --port 8000
