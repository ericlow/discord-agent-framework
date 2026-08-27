"""Create the database and apply the schema. Run once before first use.

The database name is taken from the path component of ``DATABASE_URL`` (or from
``DB_NAME`` if set). Requires ``DATABASE_URL`` to point at your Postgres server.
"""
import os
from urllib.parse import urlparse

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
DB_NAME = os.environ.get("DB_NAME") or urlparse(DATABASE_URL).path.lstrip("/")
if not DB_NAME:
    raise SystemExit("Could not determine database name from DATABASE_URL; set DB_NAME.")

# Connect to the default 'postgres' database to create ours if it doesn't exist.
base_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
conn = psycopg2.connect(base_url)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
if not cur.fetchone():
    cur.execute(f'CREATE DATABASE "{DB_NAME}"')
    print(f"Created database: {DB_NAME}")
else:
    print(f"Database already exists: {DB_NAME}")
cur.close()
conn.close()

# Apply the schema.
conn = psycopg2.connect(DATABASE_URL)
schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
with open(schema_path) as f:
    conn.cursor().execute(f.read())
conn.commit()
conn.close()
print("Schema applied.")
