import os
from datetime import datetime

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.token_refresh import ensure_valid_token


def _build_youtube_client(user):
    credentials = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    )
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


async def fetch_channel_stats(user, db: AsyncSession) -> dict:
    """Fetch subscriber count, total views, and video count for the authenticated channel."""
    user = await ensure_valid_token(user, db)
    youtube = _build_youtube_client(user)

    response = (
        youtube.channels()
        .list(part="statistics", mine=True)
        .execute()
    )

    items = response.get("items", [])
    if not items:
        return {"subscriber_count": 0, "total_views": 0, "video_count": 0}

    stats = items[0].get("statistics", {})
    return {
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
    }


async def fetch_top_videos(user, db: AsyncSession, limit: int = 5) -> list[dict]:
    """Fetch top N videos ordered by view count."""
    user = await ensure_valid_token(user, db)
    youtube = _build_youtube_client(user)

    # search.list costs 100 quota units — kept minimal (one call per snapshot)
    search_response = (
        youtube.search()
        .list(
            part="snippet",
            forMine=True,
            type="video",
            order="viewCount",
            maxResults=limit,
        )
        .execute()
    )

    items = search_response.get("items", [])
    if not items:
        return []

    video_ids = [item["id"]["videoId"] for item in items]

    videos_response = (
        youtube.videos()
        .list(part="statistics,snippet", id=",".join(video_ids))
        .execute()
    )

    result = []
    for item in videos_response.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
            or ""
        )
        published_at_str = snippet.get("publishedAt")
        published_at = None
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        result.append(
            {
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "thumbnail_url": thumbnail_url,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "published_at": published_at,
            }
        )

    return result
