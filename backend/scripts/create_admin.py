"""Bootstrap the first admin account (demo users are not seeded in production).

Usage (from backend/, with DATABASE_URL and JWT_SECRET set):
    python -m scripts.create_admin --email you@company.com --name "Your Name"

The password is read from the ADMIN_PASSWORD environment variable, or prompted for
interactively; it is never taken from the command line (shell history). Writes directly to
the `auth_users` table and exits non-zero if the database write fails.
"""

import argparse
import asyncio
import getpass
import os
import sys
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.database import async_session_factory
from app.models.models import AuthUserRecord
from app.models.user import UserRole

MIN_PASSWORD_LENGTH = 12


async def create_admin(email: str, full_name: str, password: str, tenant_id: str) -> str:
    async with async_session_factory() as session:
        existing = await session.execute(select(AuthUserRecord).where(AuthUserRecord.email == email))
        if existing.scalars().first():
            raise SystemExit(f"User {email} already exists; nothing changed.")
        user_id = f"usr-{uuid.uuid4().hex[:12]}"
        session.add(AuthUserRecord(
            id=user_id,
            email=email,
            full_name=full_name,
            role=UserRole.ADMIN.value,
            tenant_id=tenant_id,
            is_active=True,
            hashed_password=hash_password(password),
        ))
        await session.commit()
        return user_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the first admin account.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="Full name")
    parser.add_argument("--tenant", default="glg-default")
    args = parser.parse_args()

    password = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Admin password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", file=sys.stderr)
        return 1

    email = args.email.strip().lower()
    try:
        user_id = asyncio.run(create_admin(email, args.name, password, args.tenant))
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:  # database unreachable, schema missing, ...
        print(f"Failed to create admin (database write did not succeed): {exc}", file=sys.stderr)
        return 1
    print(f"Created admin {email} (id {user_id}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
