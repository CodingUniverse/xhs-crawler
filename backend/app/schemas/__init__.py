from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PlatformEnum(str, Enum):
    XHS = "xiaohongshu"
    ZHIHU = "zhihu"
    WECHAT = "wechat"
    DOUYIN = "douyin"


class TaskTypeEnum(str, Enum):
    KEYWORD = "keyword"
    AUTHOR = "author"


class AccountStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


class TaskStatusEnum(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class PlatformAccountBase(BaseModel):
    platform_name: PlatformEnum
    account_name: str
    cookie_data: str


class PlatformAccountCreate(PlatformAccountBase):
    pass


class PlatformAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    cookie_data: Optional[str] = None
    status: Optional[AccountStatusEnum] = None


class PlatformAccountResponse(PlatformAccountBase):
    id: int
    status: AccountStatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScrapeTaskBase(BaseModel):
    task_type: TaskTypeEnum
    target_value: str
    platform: PlatformEnum
    frequency: str = Field(default="0 */6 * * *")
    depth: int = Field(default=2, ge=1, le=20)
    retry_times: int = Field(default=3, ge=0, le=10)


class ScrapeTaskCreate(ScrapeTaskBase):
    pass


class ScrapeTaskUpdate(BaseModel):
    task_type: Optional[TaskTypeEnum] = None
    target_value: Optional[str] = None
    platform: Optional[PlatformEnum] = None
    frequency: Optional[str] = None
    depth: Optional[int] = None
    retry_times: Optional[int] = None
    status: Optional[TaskStatusEnum] = None


class ScrapeTaskResponse(ScrapeTaskBase):
    id: int
    status: TaskStatusEnum
    last_run_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MediaUrls(BaseModel):
    images: list[str] = []
    video: Optional[str] = None


class Metrics(BaseModel):
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0


class ContentAssetBase(BaseModel):
    platform_post_id: str
    platform: PlatformEnum
    source_url: Optional[str] = None
    title: Optional[str] = None
    content_text: Optional[str] = None
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    publish_date: Optional[datetime] = None
    media_urls: Optional[MediaUrls] = None
    metrics: Optional[Metrics] = None


class ContentAssetCreate(ContentAssetBase):
    pass


class ContentAssetUpdate(BaseModel):
    source_url: Optional[str] = None
    title: Optional[str] = None
    content_text: Optional[str] = None
    author_name: Optional[str] = None
    media_urls: Optional[MediaUrls] = None
    metrics: Optional[Metrics] = None
    is_starred: Optional[bool] = None
    is_archived: Optional[bool] = None
    manual_outline: Optional[str] = None
    ai_analysis: Optional[dict] = None


class ContentAssetResponse(ContentAssetBase):
    id: int
    is_starred: bool = False
    is_archived: bool = False
    is_deleted: bool = False
    manual_outline: Optional[str] = None
    ai_analysis: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentAssetListResponse(BaseModel):
    items: list[ContentAssetResponse]
    total: int
    page: int
    page_size: int


class QRCodeResponse(BaseModel):
    qr_code: str
    session_id: str
    status: str


class LoginStatusResponse(BaseModel):
    session_id: str
    status: str
    account_id: Optional[int] = None
    message: Optional[str] = None
