from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.database import ContentAsset, PlatformEnum
from app.schemas import (
    ContentAssetCreate,
    ContentAssetUpdate,
    ContentAssetResponse,
    ContentAssetListResponse,
)

router = APIRouter(prefix="/content", tags=["content"])


@router.get("", response_model=ContentAssetListResponse)
async def list_content(
    platform: PlatformEnum = None,
    author_name: str = None,
    search: str = None,
    is_starred: bool = None,
    is_archived: bool = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = "publish_date",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    query = select(ContentAsset)
    count_query = select(func.count(ContentAsset.id))
    
    if platform:
        query = query.where(ContentAsset.platform == platform)
        count_query = count_query.where(ContentAsset.platform == platform)
    if author_name:
        query = query.where(ContentAsset.author_name.ilike(f"%{author_name}%"))
        count_query = count_query.where(ContentAsset.author_name.ilike(f"%{author_name}%"))
    if search:
        query = query.where(
            (ContentAsset.title.ilike(f"%{search}%")) | 
            (ContentAsset.content_text.ilike(f"%{search}%"))
        )
        count_query = count_query.where(
            (ContentAsset.title.ilike(f"%{search}%")) | 
            (ContentAsset.content_text.ilike(f"%{search}%"))
        )
    if is_starred is not None:
        query = query.where(ContentAsset.is_starred == is_starred)
        count_query = count_query.where(ContentAsset.is_starred == is_starred)
    if is_archived is not None:
        query = query.where(ContentAsset.is_archived == is_archived)
        count_query = count_query.where(ContentAsset.is_archived == is_archived)
    
    if order_by == "likes":
        if sort_order == "asc":
            query = query.order_by(ContentAsset.metrics["likes"].asc().nullslast())
        else:
            query = query.order_by(ContentAsset.metrics["likes"].desc().nullslast())
    elif order_by == "comments":
        if sort_order == "asc":
            query = query.order_by(ContentAsset.metrics["comments"].asc().nullslast())
        else:
            query = query.order_by(ContentAsset.metrics["comments"].desc().nullslast())
    elif order_by == "shares":
        if sort_order == "asc":
            query = query.order_by(ContentAsset.metrics["shares"].asc().nullslast())
        else:
            query = query.order_by(ContentAsset.metrics["shares"].desc().nullslast())
    elif order_by == "views":
        if sort_order == "asc":
            query = query.order_by(ContentAsset.metrics["views"].asc().nullslast())
        else:
            query = query.order_by(ContentAsset.metrics["views"].desc().nullslast())
    else:
        if sort_order == "asc":
            query = query.order_by(ContentAsset.publish_date.asc().nullslast())
        else:
            query = query.order_by(ContentAsset.publish_date.desc().nullslast())
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return ContentAssetListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{content_id}", response_model=ContentAssetResponse)
async def get_content(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.post("", response_model=ContentAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content: ContentAssetCreate,
    db: AsyncSession = Depends(get_db),
):
    db_content = ContentAsset(**content.model_dump())
    db.add(db_content)
    await db.commit()
    await db.refresh(db_content)
    return db_content


@router.patch("/{content_id}", response_model=ContentAssetResponse)
async def update_content(
    content_id: int,
    content_update: ContentAssetUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    update_data = content_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    
    await db.commit()
    await db.refresh(content)
    return content


@router.post("/{content_id}/star", response_model=ContentAssetResponse)
async def toggle_star(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content.is_starred = not content.is_starred
    await db.commit()
    await db.refresh(content)
    
    return content


@router.post("/{content_id}/archive", response_model=ContentAssetResponse)
async def toggle_archive(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content.is_archived = not content.is_archived
    await db.commit()
    await db.refresh(content)
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    await db.delete(content)
    await db.commit()


@router.patch("/{content_id}/outline", response_model=ContentAssetResponse)
async def save_outline(
    content_id: int,
    outline: dict,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content.manual_outline = outline.get("outline", "")
    await db.commit()
    await db.refresh(content)
    
    return content


@router.post("/{content_id}/ai-analyze", response_model=dict)
async def ai_analyze(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentAsset).where(ContentAsset.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    mock_analysis = {
        "hook": "这是一个吸引眼球的开头，用来引起读者好奇心",
        "body_structure": [
            {"section": "背景介绍", "key_points": ["问题背景", "读者痛点"]},
            {"section": "核心内容", "key_points": ["解决方案", "实操步骤"]},
            {"section": "总结", "key_points": ["核心要点", "行动号召"]}
        ],
        "hot_phrases": ["必看", "震惊", "原来如此", "干货"],
        "emotion_triggers": ["好奇心", "焦虑感", "成就感"],
        "call_to_action": "快来试试吧！"
    }
    
    content.ai_analysis = mock_analysis
    await db.commit()
    await db.refresh(content)
    
    return {
        "status": "success",
        "message": "AI 拆解功能预留，待接入真实大模型 API",
        "mock_data": mock_analysis,
    }
