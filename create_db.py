import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME")

if not all([db_user, db_password, db_host, db_name]):
    print("❌ Missing required environment variables!")
    exit(1)

connection_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/"

print("⏳ Waiting for database to be reachable...")

# ---------------------------------------
# Wait Logic: Try for 30 attempts
# ---------------------------------------
for attempt in range(1, 31):
    try:
        engine = create_engine(connection_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection established.")
        break
    except OperationalError as e:
        print(f"⏳ DB not ready (attempt {attempt}/30)...")
        time.sleep(2)
else:
    print("❌ ERROR: Could not connect to database after 30 attempts.")
    exit(1)

# ---------------------------------------
# CREATE DATABASE IF NOT EXISTS
# ---------------------------------------
try:
    print(f"🛠 Creating database `{db_name}` if it does not exist...")

    engine = create_engine(connection_url)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
        print(f"✅ Database `{db_name}` created or already exists.")

except ProgrammingError as pe:
    print(f"❌ ERROR while creating database: {pe}")
    exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
    exit(1)

print("🎉 Database initialization complete.")
