from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import ScrapeTask, TaskStatusEnum, PlatformAccount, AccountStatusEnum
from app.crud.content import upsert_content_batch
from app.core.database import async_session_maker
from datetime import datetime
import json
import random
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
task_jobs = {}


async def execute_scrape_task(task_id: int) -> dict:
    async with async_session_maker() as db:
        result = await db.execute(
            select(ScrapeTask).where(ScrapeTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        if task.status != TaskStatusEnum.RUNNING:
            return {"error": "Task is not running"}

        result = await db.execute(
            select(PlatformAccount).where(
                PlatformAccount.platform_name == task.platform,
                PlatformAccount.status == AccountStatusEnum.ACTIVE,
            )
        )
        account = result.scalar_one_or_none()

        if not account:
            return {"error": "No active account for this platform"}

        try:
            if task.platform.value == "xiaohongshu":
                scrape_data = await _execute_xhs_task(db, task)
            else:
                scrape_data = generate_mock_content(
                    platform=task.platform.value,
                    target_value=task.target_value,
                    task_type=task.task_type.value,
                    depth=task.depth,
                )
            
            inserted, updated = await upsert_content_batch(
                db,
                task.platform,
                scrape_data,
            )

            task.last_run_time = datetime.utcnow()
            await db.commit()

            return {
                "task_id": task_id,
                "platform": task.platform.value,
                "target": task.target_value,
                "inserted": inserted,
                "updated": updated,
                "executed_at": task.last_run_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Task execution error: {e}")
            
            if task.retry_times and task.retry_times > 0:
                task.retry_times -= 1
            
            if "login" in str(e).lower() or "cookie" in str(e).lower():
                if account:
                    account.status = AccountStatusEnum.EXPIRED
                    await db.commit()
                
                task.status = TaskStatusEnum.PAUSED
                await db.commit()
                await remove_task_from_scheduler(task_id)
            
            return {
                "task_id": task_id,
                "error": str(e),
                "platform": task.platform.value,
                "target": task.target_value,
            }


async def _execute_xhs_task(db: AsyncSession, task: ScrapeTask) -> list[dict]:
    from app.services.xhs_scraper import scrape_xhs_task
    
    try:
        return await scrape_xhs_task(
            db=db,
            task_type=task.task_type.value,
            target_value=task.target_value,
            depth=task.depth,
        )
    except ValueError as e:
        if "No active account" in str(e):
            raise
        elif "Invalid cookie" in str(e):
            raise Exception("Login failed - invalid cookies")
        else:
            raise
    except Exception as e:
        logger.error(f"XHS scrape error: {e}")
        if "timeout" in str(e).lower():
            raise Exception("Page load timeout")
        raise


def generate_mock_content(platform: str, target_value: str, task_type: str, depth: int) -> list[dict]:
    platforms = {
        "xiaohongshu": "小红书",
        "zhihu": "知乎",
        "wechat": "公众号",
        "douyin": "抖音",
    }

    mock_items = []
    count = depth * 3

    for i in range(count):
        post_id = f"{platform}_{target_value[:8]}_{i+1}"
        mock_items.append({
            "platform_post_id": post_id,
            "title": f"{platforms.get(platform, platform)} 内容 #{i+1} - {target_value}",
            "content_text": f"这是关于 {target_value} 的第 {i+1} 条内容摘要。",
            "author_name": f"作者{i+1}",
            "author_id": f"author_{i+1}",
            "publish_date": datetime.utcnow().isoformat(),
            "media_urls": {
                "images": [f"https://example.com/image_{i+1}.jpg"],
                "video": None,
            },
            "metrics": {
                "likes": random.randint(100, 10000),
                "comments": random.randint(10, 500),
                "shares": random.randint(5, 200),
                "views": random.randint(1000, 100000),
            },
            "raw_data": {"mock": True, "task_type": task_type},
        })

    return mock_items


def parse_frequency(frequency: str) -> dict:
    try:
        parts = frequency.split()
        if len(parts) >= 5:
            return {
                "type": "cron",
                "minute": parts[0],
                "hour": parts[1],
                "day": parts[2],
                "month": parts[3],
                "day_of_week": parts[4],
            }
        elif frequency.startswith("interval:"):
            interval_parts = frequency.replace("interval:", "").split(":")
            return {
                "type": "interval",
                "hours": int(interval_parts[0]) if len(interval_parts) > 0 else 0,
                "minutes": int(interval_parts[1]) if len(interval_parts) > 1 else 0,
            }
    except Exception:
        pass

    return {"type": "interval", "hours": 1, "minutes": 0}


async def add_task_to_scheduler(task: ScrapeTask) -> None:
    job_id = f"task_{task.id}"

    if job_id in task_jobs:
        task_jobs[job_id].remove()
        del task_jobs[job_id]

    if task.status != TaskStatusEnum.RUNNING:
        return

    freq = parse_frequency(task.frequency)

    if freq["type"] == "cron":
        trigger = CronTrigger(
            minute=freq.get("minute", "0"),
            hour=freq.get("hour", "*"),
            day=freq.get("day", "*"),
            month=freq.get("month", "*"),
            day_of_week=freq.get("day_of_week", "*"),
        )
    else:
        trigger = IntervalTrigger(
            hours=freq.get("hours", 1),
            minutes=freq.get("minutes", 0),
        )

    job = scheduler.add_job(
        execute_scrape_task,
        trigger=trigger,
        args=[task.id],
        id=job_id,
        replace_existing=True,
    )

    task_jobs[job_id] = job


async def remove_task_from_scheduler(task_id: int) -> None:
    job_id = f"task_{task_id}"
    if job_id in task_jobs:
        task_jobs[job_id].remove()
        del task_jobs[job_id]


async def start_scheduler() -> None:
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(ScrapeTask).where(ScrapeTask.status == TaskStatusEnum.RUNNING)
            )
            tasks = result.scalars().all()

            for task in tasks:
                await add_task_to_scheduler(task)
    except Exception as e:
        print(f"Scheduler startup skipped (no database): {e}")

    if not scheduler.running:
        scheduler.start()


async def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
