from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.auth import get_current_user
from app.database import get_db
from app.models import User, ChannelSnapshot, VideoSnapshot
from app.schemas import ChannelKPIs, VideoItem, DashboardOverview
from app.services.youtube import fetch_channel_stats, fetch_top_videos
from app.services.analytics import fetch_watch_time

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/overview", response_model=DashboardOverview)
async def get_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.refresh_token and not current_user.access_token:
        raise HTTPException(
            status_code=402,
            detail="No stored tokens. Please re-authenticate via /auth/google/login.",
        )

    today = date.today()

    # Try cache first
    result = await db.execute(
        select(ChannelSnapshot).where(
            ChannelSnapshot.user_id == current_user.id,
            ChannelSnapshot.snapshot_date == today,
        )
    )
    snapshot = result.scalar_one_or_none()

    if snapshot:
        kpis = ChannelKPIs(
            subscriber_count=snapshot.subscriber_count,
            total_views=snapshot.total_views,
            watch_time_minutes=snapshot.total_watch_time_minutes,
            video_count=snapshot.video_count,
        )
        return DashboardOverview(kpis=kpis, snapshot_date=today, data_source="cache")

    # Live fetch
    try:
        stats = await fetch_channel_stats(current_user, db)
        watch_time = await fetch_watch_time(current_user, db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"YouTube API error: {exc}") from exc

    # Only cache the snapshot when the API returned meaningful data.
    # A zero subscriber_count AND zero video_count indicates an empty/failed
    # response — writing it would poison the cache for the rest of the day.
    if stats["subscriber_count"] > 0 or stats["video_count"] > 0:
        new_snapshot = ChannelSnapshot(
            user_id=current_user.id,
            snapshot_date=today,
            subscriber_count=stats["subscriber_count"],
            total_views=stats["total_views"],
            total_watch_time_minutes=watch_time,
            video_count=stats["video_count"],
        )
        db.add(new_snapshot)
        await db.commit()

    kpis = ChannelKPIs(
        subscriber_count=stats["subscriber_count"],
        total_views=stats["total_views"],
        watch_time_minutes=watch_time,
        video_count=stats["video_count"],
    )
    return DashboardOverview(kpis=kpis, snapshot_date=today, data_source="live")


@router.get("/dashboard/top-videos", response_model=list[VideoItem])
async def get_top_videos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.refresh_token and not current_user.access_token:
        raise HTTPException(
            status_code=402,
            detail="No stored tokens. Please re-authenticate via /auth/google/login.",
        )

    today = date.today()

    # Try cache first
    result = await db.execute(
        select(VideoSnapshot)
        .where(
            VideoSnapshot.user_id == current_user.id,
            VideoSnapshot.snapshot_date == today,
        )
        .limit(5)
    )
    snapshots = result.scalars().all()

    if snapshots:
        return [
            VideoItem(
                video_id=s.video_id,
                title=s.title,
                thumbnail_url=s.thumbnail_url,
                views=s.views,
                likes=s.likes,
                comments=s.comments,
                published_at=s.published_at,
            )
            for s in snapshots
        ]

    # Live fetch
    try:
        videos = await fetch_top_videos(current_user, db, limit=5)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"YouTube API error: {exc}") from exc

    # Only cache when the API returned at least one video with a real title.
    if videos:
        for v in videos:
            new_snap = VideoSnapshot(
                user_id=current_user.id,
                snapshot_date=today,
                video_id=v["video_id"],
                title=v["title"],
                thumbnail_url=v["thumbnail_url"],
                views=v["views"],
                likes=v["likes"],
                comments=v["comments"],
                published_at=v["published_at"],
            )
            db.add(new_snap)
        await db.commit()

    return [
        VideoItem(
            video_id=v["video_id"],
            title=v["title"],
            thumbnail_url=v["thumbnail_url"],
            views=v["views"],
            likes=v["likes"],
            comments=v["comments"],
            published_at=v["published_at"],
        )
        for v in videos
    ]
