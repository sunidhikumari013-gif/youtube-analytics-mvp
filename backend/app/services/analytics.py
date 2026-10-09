import os
from datetime import date, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.token_refresh import ensure_valid_token


def _build_analytics_client(user):
    credentials = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    )
    return build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)


async def fetch_watch_time(user, db: AsyncSession) -> int:
    """Return total estimated minutes watched over the last 28 days."""
    user = await ensure_valid_token(user, db)
    analytics = _build_analytics_client(user)

    end_date = date.today()
    start_date = end_date - timedelta(days=28)

    response = (
        analytics.reports()
        .query(
            ids="channel==MINE",
            metrics="estimatedMinutesWatched",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
        )
        .execute()
    )

    rows = response.get("rows", [])
    if not rows:
        return 0

    total = sum(int(row[0]) for row in rows)
    return total
