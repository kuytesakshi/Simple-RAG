"""Create a login user from the CLI.

Run inside docker:
    docker compose --env-file backend/.env exec backend python scripts/create_user.py <username> <password>
"""
import asyncio
import sys
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


async def main(username: str, password: str) -> None:
    async with SessionLocal() as db:
        existing = (
            await db.execute(select(User).where(User.username == username))
        ).scalar_one_or_none()
        if existing:
            print(f"User '{username}' already exists.")
            return
        db.add(User(username=username, hashed_password=hash_password(password)))
        await db.commit()
        print(f"User '{username}' created.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_user.py <username> <password>")
        raise SystemExit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
