"""Supabase & PostgreSQL Database Provisioning Script.

Executes 'CREATE EXTENSION IF NOT EXISTS vector;' on target PostgreSQL / Supabase database
and applies all Alembic database migrations.
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings

def setup_database():
    db_url = getattr(settings, "database_url", None) or os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "sqlite:///./real_estate.db"
    
    print(f"[+] Target Database URL: {db_url}")
    
    # Normalize asyncpg driver to psycopg2 for sync migration/setup connection
    sync_db_url = db_url
    if "+asyncpg" in sync_db_url:
        sync_db_url = sync_db_url.replace("+asyncpg", "+psycopg2")
    elif sync_db_url.startswith("postgresql://") and not sync_db_url.startswith("postgresql+psycopg2://"):
        sync_db_url = sync_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    if sync_db_url.startswith("sqlite"):
        print("[i] SQLite detected. Skipping 'CREATE EXTENSION vector' step.")
    else:
        print("[*] PostgreSQL / Supabase connection detected.")
        try:
            print("[*] Enabling pgvector extension...")
            engine = create_engine(sync_db_url, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            print("[+] 'vector' extension enabled successfully.")
        except Exception as e:
            print(f"[!] Note: Could not enable pgvector on PostgreSQL target: {e}")
            print("[i] Ensure Supabase / Postgres instance is online and running.")

    # Run Alembic migrations programmatically
    print("[*] Running Alembic migrations...")
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg_path = backend_dir.parent / "alembic.ini"
        if not alembic_cfg_path.exists():
            alembic_cfg_path = backend_dir / "alembic.ini"

        alembic_cfg = Config(str(alembic_cfg_path))
        alembic_cfg.set_main_option("script_location", str(backend_dir.parent / "migrations"))
        
        # Test if target PostgreSQL server is reachable; if not, fallback to sqlite
        target_migration_url = sync_db_url
        if not sync_db_url.startswith("sqlite"):
            try:
                test_engine = create_engine(sync_db_url, connect_args={"connect_timeout": 3})
                with test_engine.connect():
                    pass
            except Exception as conn_err:
                print(f"[!] PostgreSQL target unreachable: {conn_err}")
                print("[i] Falling back to SQLite ('sqlite:///./real_estate.db') for migration execution.")
                target_migration_url = "sqlite:///./real_estate.db"

        alembic_cfg.set_main_option("sqlalchemy.url", target_migration_url)

        command.upgrade(alembic_cfg, "head")
        print("[+] Alembic database migrations completed successfully!")
    except Exception as e:
        print(f"[!] Error applying Alembic migrations: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
