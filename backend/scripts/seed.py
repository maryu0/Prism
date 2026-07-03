"""Seed a demo workspace + admin user so later phases have something to point at.

The password hash here is a placeholder, not a real bcrypt hash — Phase 2 (auth)
is what makes this user able to actually log in. This script only proves the
schema and indexes work end-to-end against real collections.

Usage: python -m scripts.seed
"""

import asyncio

from bson import ObjectId

from app.core.database import get_mongo_db
from app.models import collections as c

DEMO_EMAIL = "admin@demo.prism"


async def main() -> None:
    db = get_mongo_db()

    existing = await db[c.USERS].find_one({"email": DEMO_EMAIL})
    if existing:
        print(f"Demo admin already exists: {existing['_id']}")
        return

    workspace_id = ObjectId()
    user_id = ObjectId()

    await db[c.WORKSPACES].insert_one(
        {
            "_id": workspace_id,
            "name": "Demo Workspace",
            "ownerId": user_id,
            "inviteTokens": [],
        }
    )

    await db[c.USERS].insert_one(
        {
            "_id": user_id,
            "email": DEMO_EMAIL,
            "passwordHash": "SEED_PLACEHOLDER_NOT_A_REAL_HASH",
            "name": "Demo Admin",
            "role": "admin",
            "workspaceId": workspace_id,
        }
    )

    print(f"Seeded workspace {workspace_id} and admin user {user_id} ({DEMO_EMAIL})")


if __name__ == "__main__":
    asyncio.run(main())
