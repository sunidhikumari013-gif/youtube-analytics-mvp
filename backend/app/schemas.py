from datetime import datetime, date as DateType
from typing import Optional

from pydantic import BaseModel, computed_field


class ChannelKPIs(BaseModel):
    subscriber_count: int
    total_views: int
    watch_time_minutes: int
    video_count: int


class VideoItem(BaseModel):
    video_id: str
    title: str
    thumbnail_url: str
    views: int
    likes: int
    comments: int
    published_at: Optional[datetime] = None

    @computed_field  # type: ignore[misc]
    @property
    def engagement_rate(self) -> float:
        if self.views == 0:
            return 0.0
        return round((self.likes + self.comments) / self.views * 100, 2)


class DashboardOverview(BaseModel):
    kpis: ChannelKPIs
    snapshot_date: DateType
    data_source: str  # "cache" or "live"
