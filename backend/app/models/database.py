from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index, Enum, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
import enum


class PlatformEnum(str, enum.Enum):
    XHS = "xiaohongshu"
    ZHIHU = "zhihu"
    WECHAT = "wechat"
    DOUYIN = "douyin"


class TaskTypeEnum(str, enum.Enum):
    KEYWORD = "keyword"
    AUTHOR = "author"


class AccountStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


class TaskStatusEnum(str, enum.Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class Base(DeclarativeBase):
    pass


class PlatformAccount(Base):
    __tablename__ = "platform_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_name = Column(Enum(PlatformEnum), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    cookie_data = Column(Text, nullable=False)
    status = Column(Enum(AccountStatusEnum), default=AccountStatusEnum.PENDING)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_platform_accounts_platform_status', 'platform_name', 'status'),
    )


class ScrapeTask(Base):
    __tablename__ = "scrape_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(Enum(TaskTypeEnum), nullable=False)
    target_value = Column(String(512), nullable=False)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    frequency = Column(String(64), nullable=False)
    depth = Column(Integer, default=2)
    retry_times = Column(Integer, default=3)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.PAUSED)
    last_run_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_scrape_tasks_platform_status', 'platform', 'status'),
    )


class ContentAsset(Base):
    __tablename__ = "content_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_post_id = Column(String(255), nullable=False, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    source_url = Column(String(1024), nullable=True, index=True)
    title = Column(String(1024), nullable=True)
    content_text = Column(Text, nullable=True)
    author_name = Column(String(255), nullable=True, index=True)
    author_id = Column(String(255), nullable=True)
    publish_date = Column(DateTime, nullable=True, index=True)
    media_urls = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True)
    is_starred = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)
    is_deleted = Column(Boolean, default=False, index=True)
    manual_outline = Column(Text, nullable=True)
    ai_analysis = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('ix_content_assets_platform_post', 'platform', 'platform_post_id', unique=True),
        Index('ix_content_assets_publish_desc', 'platform', 'publish_date'),
    )


class WebhookConfig(Base):
    __tablename__ = "webhook_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False)
    webhook_type = Column(String(64), nullable=False)
    secret = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
