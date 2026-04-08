from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.database import ScrapeTask, TaskStatusEnum, TaskTypeEnum, PlatformEnum
from app.schemas import (
    ScrapeTaskCreate,
    ScrapeTaskUpdate,
    ScrapeTaskResponse,
)
from app.services.scheduler import (
    add_task_to_scheduler,
    remove_task_from_scheduler,
    execute_scrape_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[ScrapeTaskResponse])
async def list_tasks(
    platform: PlatformEnum = None,
    status: TaskStatusEnum = None,
    task_type: TaskTypeEnum = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ScrapeTask)
    if platform:
        query = query.where(ScrapeTask.platform == platform)
    if status:
        query = query.where(ScrapeTask.status == status)
    if task_type:
        query = query.where(ScrapeTask.task_type == task_type)
    result = await db.execute(query.order_by(ScrapeTask.created_at.desc()))
    return result.scalars().all()


@router.get("/{task_id}", response_model=ScrapeTaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScrapeTask).where(ScrapeTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=ScrapeTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: ScrapeTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    db_task = ScrapeTask(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    if db_task.status == TaskStatusEnum.RUNNING:
        await add_task_to_scheduler(db_task)

    return db_task


@router.patch("/{task_id}", response_model=ScrapeTaskResponse)
async def update_task(
    task_id: int,
    task_update: ScrapeTaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScrapeTask)
        .where(ScrapeTask.id == task_id)
        .with_for_update()
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)

    if "status" in update_data:
        if task.status == TaskStatusEnum.RUNNING:
            await add_task_to_scheduler(task)
        else:
            await remove_task_from_scheduler(task.id)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScrapeTask)
        .where(ScrapeTask.id == task_id)
        .with_for_update()
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await remove_task_from_scheduler(task_id)
    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/run", response_model=ScrapeTaskResponse)
async def run_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScrapeTask)
        .where(ScrapeTask.id == task_id)
        .with_for_update()
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = TaskStatusEnum.RUNNING
    await db.commit()
    await db.refresh(task)

    await add_task_to_scheduler(task)

    return task


@router.post("/{task_id}/pause", response_model=ScrapeTaskResponse)
async def pause_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScrapeTask)
        .where(ScrapeTask.id == task_id)
        .with_for_update()
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = TaskStatusEnum.PAUSED
    await db.commit()
    await db.refresh(task)

    await remove_task_from_scheduler(task_id)

    return task


@router.post("/{task_id}/toggle", response_model=ScrapeTaskResponse)
async def toggle_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScrapeTask)
        .where(ScrapeTask.id == task_id)
        .with_for_update()
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == TaskStatusEnum.RUNNING:
        task.status = TaskStatusEnum.PAUSED
        await remove_task_from_scheduler(task_id)
    else:
        task.status = TaskStatusEnum.RUNNING
        await add_task_to_scheduler(task)
    
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/execute", response_model=dict)
async def execute_task_now(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScrapeTask).where(ScrapeTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    result_data = await execute_scrape_task(task_id)
    return result_data
