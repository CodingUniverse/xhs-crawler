from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import ContentAsset, PlatformEnum
from app.schemas import ContentAssetCreate, ContentAssetUpdate
from datetime import datetime
import json


async def upsert_content(
    db: AsyncSession,
    platform: PlatformEnum,
    platform_post_id: str,
    data: dict,
) -> tuple[ContentAsset, bool]:
    result = await db.execute(
        select(ContentAsset).where(
            ContentAsset.platform == platform,
            ContentAsset.platform_post_id == platform_post_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        update_data = {
            "metrics": data.get("metrics"),
            "updated_at": datetime.utcnow(),
        }
        if data.get("title"):
            update_data["title"] = data["title"]
        if data.get("content_text"):
            update_data["content_text"] = data["content_text"]
        if data.get("media_urls"):
            update_data["media_urls"] = data["media_urls"]
        if data.get("source_url"):
            update_data["source_url"] = data["source_url"]

        for field, value in update_data.items():
            if value is not None:
                setattr(existing, field, value)

        await db.commit()
        await db.refresh(existing)
        return existing, False

    new_content = ContentAsset(
        platform_post_id=platform_post_id,
        platform=platform,
        source_url=data.get("source_url"),
        title=data.get("title"),
        content_text=data.get("content_text"),
        author_name=data.get("author_name"),
        author_id=data.get("author_id"),
        publish_date=data.get("publish_date"),
        media_urls=data.get("media_urls"),
        metrics=data.get("metrics"),
        raw_data=data.get("raw_data"),
    )
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)
    return new_content, True


async def upsert_content_batch(
    db: AsyncSession,
    platform: PlatformEnum,
    items: list[dict],
) -> tuple[int, int]:
    inserted = 0
    updated = 0

    for item in items:
        _, is_new = await upsert_content(
            db,
            platform,
            item["platform_post_id"],
            item,
        )
        if is_new:
            inserted += 1
        else:
            updated += 1

    return inserted, updated
