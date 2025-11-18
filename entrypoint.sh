#!/bin/sh
set -e

echo "Ensuring database exists"
python create_db.py

echo "Running migrations"
flask db upgrade

echo "Starting gunicorn server"
exec gunicorn run:app -w 4 -b 0.0.0.0:8000 --log-file -