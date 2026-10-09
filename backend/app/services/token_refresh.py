import os
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


async def ensure_valid_token(user, db: AsyncSession):
    """Check token expiry and refresh if needed. Returns the (possibly updated) user."""
    now = datetime.now(timezone.utc)
    expiry = user.token_expiry
    if expiry is not None:
        # Make naive datetime timezone-aware for comparison
        if expiry.tzinfo is None:
            from datetime import timezone as tz
            expiry = expiry.replace(tzinfo=tz.utc)
        if expiry > now:
            return user  # Token still valid

    if not user.refresh_token:
        raise ValueError(f"No refresh token available for user {user.id}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": user.refresh_token,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    from datetime import timedelta
    user.access_token = data["access_token"]
    user.token_expiry = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
    await db.commit()
    await db.refresh(user)
    return user
