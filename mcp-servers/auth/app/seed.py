"""Bootstrap an admin user from env if AUTH_BOOTSTRAP_ADMIN_* vars are set."""
from __future__ import annotations

import logging

from sqlalchemy import select

from .config import settings
from .db import SessionLocal
from .models import User
from .security import hash_password

logger = logging.getLogger("auth-mcp.seed")


async def seed_admin() -> None:
    email = (settings.bootstrap_admin_email or "").strip().lower()
    password = settings.bootstrap_admin_password
    if not email or not password:
        return
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        if user is None:
            session.add(
                User(email=email, password_hash=hash_password(password), role="admin")
            )
            await session.commit()
            logger.info("bootstrapped admin user %s", email)
            return
        if user.role != "admin":
            user.role = "admin"
            await session.commit()
            logger.info("promoted existing user %s to admin", email)
