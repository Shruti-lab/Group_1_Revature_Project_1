#!/bin/sh
set -e

echo "Ensuring database exists"
python create_db.py

echo "Resetting migration tracking (preserving data)"
python -c "
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    try:
        # Only reset the migration tracking table, not actual data tables
        db.session.execute(text('DROP TABLE IF EXISTS alembic_version'))
        db.session.commit()
        print('Migration tracking reset - data preserved')
        
        # Create any missing tables (won't affect existing ones with data)
        db.create_all()
        print('Missing tables created if needed')
    except Exception as e:
        print('Error during setup:', e)
"

echo "Starting gunicorn server"
exec gunicorn run:app -w 4 -b 0.0.0.0:8000 --log-file -