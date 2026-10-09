import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(misfire_grace_time=3600)


async def daily_snapshot_job():
    """Run daily at 00:05 to snapshot all users' channel and video data."""
    from app.database import AsyncSessionLocal
    from app.models import User, ChannelSnapshot, VideoSnapshot
    from app.services.token_refresh import ensure_valid_token
    from app.services.youtube import fetch_channel_stats, fetch_top_videos
    from app.services.analytics import fetch_watch_time

    today = date.today()
    logger.info("Starting daily snapshot job for %s", today)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            try:
                if not user.refresh_token:
                    logger.warning("Skipping user %s — no refresh token", user.id)
                    continue

                user = await ensure_valid_token(user, db)

                # Channel snapshot
                existing_channel = await db.execute(
                    select(ChannelSnapshot).where(
                        ChannelSnapshot.user_id == user.id,
                        ChannelSnapshot.snapshot_date == today,
                    )
                )
                if existing_channel.scalar_one_or_none() is None:
                    stats = await fetch_channel_stats(user, db)
                    watch_time = await fetch_watch_time(user, db)
                    db.add(
                        ChannelSnapshot(
                            user_id=user.id,
                            snapshot_date=today,
                            subscriber_count=stats["subscriber_count"],
                            total_views=stats["total_views"],
                            total_watch_time_minutes=watch_time,
                            video_count=stats["video_count"],
                        )
                    )

                # Video snapshots
                existing_videos = await db.execute(
                    select(VideoSnapshot).where(
                        VideoSnapshot.user_id == user.id,
                        VideoSnapshot.snapshot_date == today,
                    )
                )
                if not existing_videos.scalars().all():
                    videos = await fetch_top_videos(user, db, limit=5)
                    for v in videos:
                        db.add(
                            VideoSnapshot(
                                user_id=user.id,
                                snapshot_date=today,
                                video_id=v["video_id"],
                                title=v["title"],
                                thumbnail_url=v["thumbnail_url"],
                                views=v["views"],
                                likes=v["likes"],
                                comments=v["comments"],
                                published_at=v["published_at"],
                            )
                        )

                await db.commit()
                logger.info("Snapshot complete for user %s", user.id)

            except Exception:
                logger.exception("Snapshot failed for user %s", user.id)

    logger.info("Daily snapshot job finished")


scheduler.add_job(daily_snapshot_job, "cron", hour=0, minute=5)
