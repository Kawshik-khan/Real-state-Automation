import os
import re
import sys
from logging.config import fileConfig

# Guarantee project root / backend root is in sys.path so 'app' is always importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
for candidate in (BACKEND_DIR, BASE_DIR, os.path.abspath(os.getcwd())):
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import shared Base — load all core domain models into metadata
from app.models.models import Base
try:
    import app.models.ai_control_plane  # ensure AI Control Plane tables are registered in metadata
except ImportError:
    pass


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Normalise DATABASE_URL for Alembic (sync driver vs asyncpg)
_raw_url = (os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url") or "").strip()
_sync_url = re.sub(r"\+asyncpg", "", _raw_url)
_sync_url = re.sub(r"^postgres://", "postgresql://", _sync_url)
config.set_main_option("sqlalchemy.url", _sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    except Exception as exc:
        print(f"[alembic] Notice: Database unreachable or migrations skipped: {exc}")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
