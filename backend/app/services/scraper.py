import asyncio
import json
import random
from typing import Optional, List, Dict
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)


class PlatformScraper:
    
    def __init__(self, cookies: Optional[List[dict]] = None, proxy: Optional[str] = None):
        self.cookies = cookies or []
        self.proxy = proxy
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.collected_data: List[dict] = []
    
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
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1280,720",
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
    
    async def scrape_xhs_note(self, note_id: str) -> Optional[dict]:
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        
        try:
            await self.page.goto(note_url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(3000)
            
            data = await self.page.evaluate("""
                () => {
                    if (window.__INITIAL_DATA__) {
                        return window.__INITIAL_DATA__;
                    }
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        if (script.textContent && (
                            script.textContent.includes('"note_id"') || 
                            script.textContent.includes('"title"')
                        )) {
                            try {
                                const text = script.textContent;
                                const match = text.match(/\\{.*\\}/);
                                if (match) {
                                    return JSON.parse(match[0]);
                                }
                            } catch (e) {}
                        }
                    }
                    const title = document.querySelector('meta[property="og:title"]')?.content || document.title;
                    const desc = document.querySelector('meta[property="og:description"]')?.content;
                    return { title, desc };
                }
            """)
            
            if data:
                return self._parse_xhs_note_data(data, note_id)
            
        except Exception as e:
            logger.error(f"Error scraping XHS note {note_id}: {e}")
        
        return None
    
    async def scrape_xhs_author(self, author_id: str, depth: int = 1) -> List[dict]:
        author_url = f"https://www.xiaohongshu.com/user/profile/{author_id}"
        
        try:
            await self.page.goto(author_url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)
            
            for _ in range(depth * 3):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.7)")
                await asyncio.sleep(random.uniform(1, 2))
            
            data = await self.page.evaluate("""
                () => {
                    if (window.__INITIAL_DATA__) {
                        return window.__INITIAL_DATA__;
                    }
                    return null;
                }
            """)
            
            if data:
                items = []
                if isinstance(data, dict):
                    if data.get("items"):
                        items = data["items"]
                    elif data.get("data", {}).get("items"):
                        items = data["data"]["items"]
                
                for item in items:
                    note = item.get("note_card") or item.get("note") or item
                    if note:
                        parsed = self._parse_xhs_note_data(note, note.get("note_id", ""))
                        if parsed:
                            self.collected_data.append(parsed)
            
        except Exception as e:
            logger.error(f"Error scraping XHS author {author_id}: {e}")
        
        return self.collected_data
    
    def _parse_xhs_note_data(self, data: dict, note_id: str) -> Optional[dict]:
        try:
            note = data.get("note", {}) or data
            
            note_id = note.get("note_id", note_id)
            if not note_id:
                return None
            
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
            
            return {
                "platform_post_id": note_id,
                "title": title or (desc[:100] if desc else ""),
                "content_text": desc,
                "author_name": user.get("nickname", ""),
                "author_id": user.get("user_id", ""),
                "publish_date": publish_date,
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
        except Exception as e:
            logger.error(f"Error parsing XHS note: {e}")
            return None
    
    async def scrape_zhihu_article(self, article_id: str) -> Optional[dict]:
        try:
            await self.page.goto(f"https://www.zhihu.com/answer/{article_id}", wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(3000)
            
            data = await self.page.evaluate("""
                () => {
                    const title = document.querySelector('h1')?.textContent;
                    const content = document.querySelector('.RichText')?.innerHTML || document.querySelector('.答案')?.innerHTML;
                    const author = document.querySelector('.AuthorInfo-name')?.textContent;
                    const voteup = document.querySelector('.VoteButton')?.textContent || '0';
                    const comments = document.querySelector('.CommentCount')?.textContent || '0';
                    return { title, content, author, voteup, comments };
                }
            """)
            
            if data:
                return self._parse_zhihu_article_data(data, article_id)
            
        except Exception as e:
            logger.error(f"Error scraping Zhihu article {article_id}: {e}")
        
        return None
    
    async def scrape_zhihu_author(self, author_id: str, depth: int = 1) -> List[dict]:
        author_url = f"https://www.zhihu.com/people/{author_id}"
        
        try:
            await self.page.goto(author_url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)
            
            for _ in range(depth * 3):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.7)")
                await asyncio.sleep(random.uniform(1, 2))
            
            data = await self.page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.List-item, .List-itemTpl, [class*="List-item"]');
                    const articles = [];
                    items.forEach(item => {
                        const title = item.querySelector('a')?.textContent || item.querySelector('h2')?.textContent;
                        const link = item.querySelector('a')?.href;
                        if (title && link) {
                            articles.push({ title, link });
                        }
                    });
                    return articles;
                }
            """)
            
            for item in data:
                article_id = item.get("link", "").split("/")[-1]
                if article_id:
                    article = await self.scrape_zhihu_article(article_id)
                    if article:
                        self.collected_data.append(article)
            
        except Exception as e:
            logger.error(f"Error scraping Zhihu author {author_id}: {e}")
        
        return self.collected_data
    
    def _parse_zhihu_article_data(self, data: dict, article_id: str) -> Optional[dict]:
        try:
            voteup_str = str(data.get("voteup", "0")).replace(",", "").strip()
            comments_str = str(data.get("comments", "0")).replace(",", "").strip()
            
            return {
                "platform_post_id": article_id,
                "title": data.get("title", ""),
                "content_text": data.get("content", ""),
                "author_name": data.get("author", ""),
                "author_id": "",
                "publish_date": datetime.utcnow(),
                "media_urls": {"images": [], "video": None},
                "metrics": {
                    "likes": int(voteup_str) if voteup_str.isdigit() else 0,
                    "comments": int(comments_str) if comments_str.isdigit() else 0,
                    "shares": 0,
                    "views": 0,
                },
                "raw_data": data,
            }
        except Exception as e:
            logger.error(f"Error parsing Zhihu article: {e}")
            return None
    
    def get_collected_data(self) -> List[dict]:
        return self.collected_data


async def load_account_cookies_by_platform(db, platform: str) -> list[dict]:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.models.database import PlatformAccount, AccountStatusEnum, PlatformEnum
    
    platform_map = {
        "xiaohongshu": PlatformEnum.XHS,
        "zhihu": PlatformEnum.ZHIHU,
    }
    
    platform_enum = platform_map.get(platform.lower(), PlatformEnum.XHS)
    
    try:
        result = await db.execute(
            select(PlatformAccount).where(
                PlatformAccount.platform_name == platform_enum,
                PlatformAccount.status == AccountStatusEnum.ACTIVE,
            ).limit(1)
        )
        account = result.scalar_one_or_none()
    except Exception:
        return []
    
    if not account:
        return []
    
    try:
        cookies = json.loads(account.cookie_data)
        return cookies
    except:
        return []
