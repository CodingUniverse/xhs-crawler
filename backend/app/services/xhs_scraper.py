import asyncio
import json
import random
from typing import Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)


class XHSScraper:
    SEARCH_API = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
    USER_POST_API = "edith.xiaohongshu.com/api/sns/web/v1/user/posted"
    CREATOR_PAGE = "https://creator.xiaohongshu.com"
    
    def __init__(self, cookies: list[dict], proxy: Optional[str] = None):
        self.cookies = cookies
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.collected_data: list[dict] = []
        self._stop_scrolling = False
    
    async def __aenter__(self):
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
            ]
        )
        
        context_options = {
            "viewport": {"width": 1280, "height": 720},
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        if self.proxy:
            context_options["proxy"] = {"server": self.proxy}
        
        self.context = await self.browser.new_context(**context_options)
        
        for cookie in self.cookies:
            await self.context.add_cookies([cookie])
        
        self.page = await self.context.new_page()
        
        self.page.on("response", self._handle_response)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    def _handle_response(self, response):
        url = response.url
        try:
            if "search/notes" in url or "user/posted" in url:
                if response.status == 200:
                    data = response.json()
                    self._parse_api_response(data, url)
        except Exception as e:
            logger.debug(f"Response handling error: {e}")
    
    def _parse_api_response(self, data: dict, url: str):
        try:
            if "search/notes" in url:
                items = data.get("data", {}).get("items", [])
                for item in items:
                    note_card = item.get("note_card", {})
                    if note_card:
                        self._extract_note_data(note_card)
            
            elif "user/posted" in url:
                items = data.get("data", {}).get("items", [])
                for item in items:
                    note = item.get("note", {})
                    if note:
                        self._extract_note_data(note)
        except Exception as e:
            logger.debug(f"Parse error: {e}")
    
    def _extract_note_data(self, note: dict):
        try:
            note_id = note.get("note_id", "")
            if not note_id:
                return
            
            user = note.get("user", {})
            interact_info = note.get("interact_info", {})
            image_list = note.get("image_list", [])
            video_info = note.get("video_info", {})
            
            title = note.get("title", "")
            desc = note.get("desc", "")
            
            images = []
            for img in image_list:
                url_info = img.get("url", {})
                if url_info.get("url"):
                    images.append(url_info["url"])
            
            video_url = None
            if video_info:
                video_url = video_info.get("url") or video_info.get("play_url")
            
            publish_time = note.get("time")
            if publish_time:
                try:
                    publish_date = datetime.fromtimestamp(publish_time)
                except:
                    publish_date = datetime.utcnow()
            else:
                publish_date = datetime.utcnow()
            
            item_data = {
                "platform_post_id": note_id,
                "title": title or desc[:100] if desc else "",
                "content_text": desc,
                "author_name": user.get("nickname", ""),
                "author_id": user.get("user_id", ""),
                "publish_date": publish_date.isoformat(),
                "media_urls": {
                    "images": images,
                    "video": video_url,
                },
                "metrics": {
                    "likes": int(interact_info.get("liked_count", 0) or 0),
                    "comments": int(interact_info.get("comment_count", 0) or 0),
                    "shares": int(interact_info.get("share_count", 0) or 0),
                    "views": int(interact_info.get("play_count", 0) or 0) if interact_info.get("play_count") else 0,
                },
                "raw_data": note,
            }
            
            self.collected_data.append(item_data)
        except Exception as e:
            logger.debug(f"Extract error: {e}")
    
    async def scrape_author(self, author_id: str, depth: int = 2) -> list[dict]:
        if not self.page:
            raise RuntimeError("Scraper not initialized")
        
        author_url = f"https://www.xiaohongshu.com/user/profile/{author_id}"
        
        await self.page.goto(author_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))
        
        await self._smooth_scroll(depth)
        
        return self.collected_data
    
    async def scrape_keyword(self, keyword: str, depth: int = 2) -> list[dict]:
        if not self.page:
            raise RuntimeError("Scraper not initialized")
        
        search_url = f"https://www.xiaohongshu.com/search_result?type=51&keyword={keyword}"
        
        await self.page.goto(search_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(random.uniform(2, 4))
        
        await self._smooth_scroll(depth)
        
        return self.collected_data
    
    async def _smooth_scroll(self, depth: int):
        self._stop_scrolling = False
        scroll_count = 0
        max_scrolls = depth * 5
        
        for _ in range(max_scrolls):
            if self._stop_scrolling:
                break
            
            await self.page.evaluate("""
                () => {
                    window.scrollBy(0, window.innerHeight * 0.7);
                }
            """)
            
            await asyncio.sleep(random.uniform(1.5, 3.0))
            scroll_count += 1
            
            if scroll_count >= max_scrolls:
                self._stop_scrolling = True
    
    def get_collected_data(self) -> list[dict]:
        return self.collected_data


async def load_account_cookies(db: AsyncSession, platform: str) -> list[dict]:
    from app.models.database import PlatformAccount, AccountStatusEnum, PlatformEnum
    
    platform_enum = PlatformEnum.XHS if platform == "xiaohongshu" else PlatformEnum(platform)
    
    result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.platform_name == platform_enum,
            PlatformAccount.status == AccountStatusEnum.ACTIVE,
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise ValueError(f"No active account for platform {platform}")
    
    try:
        cookies = json.loads(account.cookie_data)
        return cookies
    except:
        raise ValueError("Invalid cookie data")


async def scrape_xhs_task(
    db: AsyncSession,
    task_type: str,
    target_value: str,
    depth: int = 2,
) -> list[dict]:
    cookies = await load_account_cookies(db, "xiaohongshu")
    
    try:
        async with XHSScraper(cookies) as scraper:
            if task_type == "author":
                author_id = target_value
                if "xiaohongshu.com" in target_value:
                    parts = target_value.split("/")
                    author_id = parts[-1] if parts else target_value
                return await scraper.scrape_author(author_id, depth)
            else:
                return await scraper.scrape_keyword(target_value, depth)
    except Exception as e:
        logger.error(f"XHS scraper error: {e}")
        raise
