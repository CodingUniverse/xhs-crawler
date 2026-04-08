import asyncio
import json
import random
import re
from typing import Optional, List, Dict
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)

DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class PlatformScraper:
    
    def __init__(self, cookies: Optional[List[dict]] = None, proxy: Optional[str] = None, account_id: Optional[int] = None, db=None):
        self.cookies = cookies or []
        self.proxy = proxy
        self.account_id = account_id
        self.db = db
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.collected_data: List[dict] = []
        self._consecutive_failures = 0
    
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
        
        random_ua = random.choice(DESKTOP_USER_AGENTS)
        
        context_options = {
            "viewport": {"width": 1280, "height": 720},
            "user_agent": random_ua,
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "geolocation": {"latitude": 31.2304, "longitude": 121.4737},
        }
        
        if self.proxy:
            context_options["proxy"] = {"server": self.proxy}
        
        self.context = await self.browser.new_context(**context_options)
        
        for cookie in self.cookies:
            try:
                await self.context.add_cookies([cookie])
            except:
                pass
        
        self.page = await self.context.new_page()
        return self
    
    async def _trigger_circuit_breaker(self):
        if self.account_id and self.db:
            try:
                from sqlalchemy import select, update
                from app.models.database import PlatformAccount, AccountStatusEnum
                
                stmt = update(PlatformAccount).where(
                    PlatformAccount.id == self.account_id
                ).values(status=AccountStatusEnum.EXPIRED)
                
                await self.db.execute(stmt)
                await self.db.commit()
                
                logger.warning(f"🔴 账号异常，触发反爬，请及时更换 Cookie (account_id: {self.account_id})")
                print(f"\n{'='*60}")
                print(f"🔴 账号异常，触发反爬，请及时更换 Cookie")
                print(f"🔴 账号ID: {self.account_id} 已标记为过期")
                print(f"{'='*60}\n")
            except Exception as e:
                logger.error(f"Failed to mark account as expired: {e}")
    
    async def _check_and_circuit_break(self, html: str, url: str = "") -> bool:
        is_login_page = 'login' in html.lower() or '/login' in html.lower()
        is_captcha = 'captcha' in html.lower() or '验证' in html or '/captcha' in url.lower()
        
        if is_login_page or is_captcha:
            self._consecutive_failures += 1
            if self._consecutive_failures >= 2:
                await self._trigger_circuit_breaker()
            return True
        
        self._consecutive_failures = 0
        return False
    
    async def _random_sleep(self, min_sec: float = 2.0, max_sec: float = 6.0):
        sleep_time = random.uniform(min_sec, max_sec)
        await asyncio.sleep(sleep_time)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        if self.page:
            try:
                await self.page.close()
            except:
                pass
        if self.context:
            try:
                await self.context.close()
            except:
                pass
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
    
    async def scrape_xhs_note(self, note_id_or_url: str) -> Optional[dict]:
        target_url = note_id_or_url if note_id_or_url.startswith('http') else f"https://www.xiaohongshu.com/explore/{note_id_or_url}"
        
        try:
            await self._random_sleep()
            await self.page.goto(target_url, wait_until="networkidle", timeout=60000)
            
            current_url = self.page.url
            logger.info(f"Initial URL: {current_url}")
            
            final_note_id = None
            is_short_url = 'xhslink.com' in target_url or '/discovery/item/' in target_url
            
            if is_short_url:
                max_wait = 10
                waited = 0
                while waited < max_wait:
                    await asyncio.sleep(1)
                    current_url = self.page.url
                    
                    if 'xiaohongshu.com/explore/' in current_url or 'xiaohongshu.com/discovery/item/' in current_url:
                        break
                    waited += 1
                
                logger.info(f"Redirected URL: {current_url}")
            
            url_match = re.search(r'/explore/([a-zA-Z0-9]+)|/discovery/item/([a-zA-Z0-9]+)', current_url)
            if url_match:
                final_note_id = url_match.group(1) or url_match.group(2)
            else:
                parsed = urlparse(current_url)
                query_params = parse_qs(parsed.query)
                if 'note' in query_params:
                    final_note_id = query_params['note'][0]
            
            if not final_note_id:
                raise ValueError(f"未能从 URL 中提取 note_id: {current_url}")
            
            logger.info(f"Target note_id: {final_note_id}")
            
            html_content = await self.page.content()
            
            if await self._check_and_circuit_break(html_content, current_url):
                logger.warning(f"XHS note {final_note_id} - login/captcha detected")
            
            state_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*</script>', html_content)
            
            if not state_match:
                raise ValueError("抓取失败，未找到初始状态，账号可能被风控或被重定向到首页")
            
            try:
                state_data = json.loads(state_match.group(1))
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 解析失败: {e}")
            
            target_note = None
            
            if "note" in state_data and "noteDetailMap" in state_data.get("note", {}):
                note_detail_map = state_data["note"]["noteDetailMap"]
                target_note = note_detail_map.get(final_note_id, {}).get("note", {})
            
            if not target_note:
                if "note" in state_data and "note" in state_data.get("note", {}):
                    direct_note = state_data["note"]["note"]
                    if direct_note.get("note_id") == final_note_id:
                        target_note = direct_note
            
            if not target_note:
                raise ValueError(f"数据错位，未能精准匹配到目标笔记 note_id={final_note_id}")
            
            title = target_note.get("title", "") or target_note.get("desc", "")[:100]
            content_text = target_note.get("desc", "")
            
            user_info = target_note.get("user", {})
            author_name = user_info.get("nickname", "")
            author_id = user_info.get("user_id", "")
            
            interact_info = target_note.get("interact_info", {})
            likes = int(interact_info.get("liked_count", 0) or 0)
            comments = int(interact_info.get("comment_count", 0) or 0)
            shares = int(interact_info.get("share_count", 0) or 0)
            views = int(interact_info.get("play_count", 0) or 0)
            
            image_list = target_note.get("image_list", [])
            images = []
            for img in image_list:
                if isinstance(img, str) and img.startswith("http"):
                    images.append(img)
                elif isinstance(img, dict):
                    url_info = img.get("url") or {}
                    if isinstance(url_info, str) and url_info.startswith("http"):
                        images.append(url_info)
                    elif isinstance(url_info, dict) and url_info.get("url"):
                        images.append(url_info["url"])
            
            return {
                "platform_post_id": final_note_id,
                "source_url": current_url,
                "title": title,
                "content_text": content_text,
                "author_name": author_name,
                "author_id": author_id,
                "publish_date": datetime.utcnow(),
                "media_urls": {"images": images, "video": None},
                "metrics": {
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "views": views,
                },
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error scraping XHS note: {e}")
        
        return None
    
    async def scrape_xhs_from_short_url(self, short_url: str) -> Optional[dict]:
        try:
            return await self.scrape_xhs_note(short_url)
        except Exception as e:
            logger.error(f"Error resolving XHS short URL {short_url}: {e}")
        return None
    
    async def scrape_xhs_author(self, author_id: str, depth: int = 1) -> List[dict]:
        author_url = f"https://www.xiaohongshu.com/user/profile/{author_id}"
        
        try:
            await self._random_sleep()
            await self.page.goto(author_url, wait_until="networkidle", timeout=60000)
            await self.page.wait_for_timeout(3000)
            
            html = await self.page.content()
            if await self._check_and_circuit_break(html, author_url):
                logger.warning(f"XHS author {author_id} - login/captcha detected")
            
            for _ in range(depth * 3):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.7)")
                await asyncio.sleep(random.uniform(1, 2))
            
            data = await self.page.evaluate("""
                () => {
                    const data = window.__UNIVERSAL_DATA__ || window.__INITIAL_DATA__ || {};
                    return data.items || data.data?.items || data.notes || [];
                }
            """)
            
            for item in data:
                note = item.get("note_card") or item.get("note") or item
                if note:
                    note_id = note.get("note_id")
                    if note_id:
                        parsed = self._parse_xhs_note_data(note, note_id)
                        if parsed:
                            self.collected_data.append(parsed)
            
        except Exception as e:
            logger.error(f"Error scraping XHS author {author_id}: {e}")
        
        return self.collected_data
    
    def _parse_xhs_note_data(self, data: dict, note_id: str) -> Optional[dict]:
        try:
            if isinstance(data, list):
                if len(data) > 0:
                    data = data[0]
            
            note = data.get("note") or data
            if not note:
                note = data
            
            note_id = str(note.get("note_id") or note_id or "")
            if not note_id:
                return None
            
            user = note.get("user") or {}
            interact_info = note.get("interact_info") or {}
            image_list = note.get("image_list") or []
            
            title = note.get("title", "") or data.get("title", "")
            desc = note.get("desc", "") or note.get("content", "") or data.get("desc", "")
            
            images = []
            for img in image_list:
                if isinstance(img, str) and img.startswith("http"):
                    images.append(img)
                elif isinstance(img, dict):
                    url_info = img.get("url") or {}
                    if isinstance(url_info, str) and url_info.startswith("http"):
                        images.append(url_info)
                    elif isinstance(url_info, dict) and url_info.get("url"):
                        images.append(url_info["url"])
            
            def parse_number(val):
                if not val:
                    return 0
                try:
                    return int(str(val).replace(",", ""))
                except:
                    return 0
            
            return {
                "platform_post_id": note_id,
                "title": title or (desc[:100] if desc else f"笔记 {note_id}"),
                "content_text": desc,
                "author_name": user.get("nickname", "") or data.get("author", ""),
                "author_id": str(user.get("user_id", "") or data.get("author_id", "")),
                "publish_date": datetime.utcnow(),
                "media_urls": {"images": images, "video": None},
                "metrics": {
                    "likes": parse_number(interact_info.get("liked_count") or data.get("likes")),
                    "comments": parse_number(interact_info.get("comment_count") or data.get("comments")),
                    "shares": parse_number(interact_info.get("share_count") or data.get("shares")),
                    "views": parse_number(interact_info.get("play_count") or data.get("views")),
                },
            }
        except Exception as e:
            logger.error(f"Error parsing XHS note: {e}")
            return None
    
    async def scrape_zhihu_article(self, article_id: str) -> Optional[dict]:
        if article_id.startswith('https://'):
            article_url = article_id
        elif 'zhuanlan.zhihu.com' in article_id or 'zhihu.com' in article_id:
            if article_id.startswith('/'):
                article_id = article_id.lstrip('/')
            article_url = f"https://www.zhihu.com/{article_id}"
        else:
            article_url = f"https://www.zhihu.com/answer/{article_id}"
        
        try:
            await self._random_sleep()
            await self.page.goto(article_url, wait_until="networkidle", timeout=60000)
            await self.page.wait_for_timeout(3000)
            
            html = await self.page.content()
            if await self._check_and_circuit_break(html, article_url):
                logger.warning(f"Zhihu article {article_id} - login/captcha detected")
            
            data = await self.page.evaluate("""
                () => {
                    const result = {};
                    
                    const titleSelectors = [
                        'h1', '.Post-title', '.QuestionHeader-title', 
                        '.QuestionHeader-content .RichText', '[class*="title"]'
                    ];
                    for (const sel of titleSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            result.title = el.textContent.trim();
                            break;
                        }
                    }
                    
                    const contentSelectors = [
                        '.RichText', '.Post-content', '.Answer-content',
                        '.QuestionBody', '[class*="content"]', '.zm-editable-content'
                    ];
                    for (const sel of contentSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.innerHTML) {
                            result.content = el.innerHTML;
                            break;
                        }
                    }
                    
                    const authorSelectors = [
                        '.AuthorInfo-name', '.Post-author', '[class*="author"] .name',
                        '.UserLink-name', '.zm-rich-text-author'
                    ];
                    for (const sel of authorSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            result.author = el.textContent.trim();
                            break;
                        }
                    }
                    
                    const voteSelectors = [
                        '.VoteButton', '.up-btn', '[class*="vote"] .count',
                        '.zm-vote-btn .count'
                    ];
                    for (const sel of voteSelectors) {
                        const el = document.querySelector(sel);
                        if (el && el.textContent.trim()) {
                            result.voteup = el.textContent.trim();
                            break;
                        }
                    }
                    
                    return result;
                }
            """)
            
            if data and data.get("title"):
                return self._parse_zhihu_article_data(data, article_id, article_url)
            
            page_html = await self.page.content()
            is_blocked = 'captcha' in page_html.lower() or '验证' in page_html or '登录' in page_html[:5000]
            
            return {
                "platform_post_id": str(article_id),
                "source_url": article_url,
                "title": f"知乎文章 {article_id}",
                "content_text": "⚠️ 页面被拦截或需登录才能查看内容。请在账户管理中添加已登录的知乎Cookie后再试。" if is_blocked else "⚠️ 无法提取页面内容，可能是反爬措施或页面结构变化。",
                "author_name": data.get("author", "") if data else "",
                "author_id": "",
                "publish_date": datetime.utcnow(),
                "media_urls": {"images": [], "video": None},
                "metrics": {"likes": 0, "comments": 0, "shares": 0, "views": 0},
            }
            
        except Exception as e:
            logger.error(f"Error scraping Zhihu article {article_id}: {e}")
        
        return None
    
    async def scrape_zhihu_author(self, author_id: str, depth: int = 1) -> List[dict]:
        return self.collected_data
    
    def _parse_zhihu_article_data(self, data: dict, article_id: str, article_url: str) -> Optional[dict]:
        try:
            voteup_str = str(data.get("voteup", "0")).replace(",", "").strip()
            
            return {
                "platform_post_id": str(article_id),
                "source_url": article_url,
                "title": data.get("title", ""),
                "content_text": data.get("content", ""),
                "author_name": data.get("author", ""),
                "author_id": "",
                "publish_date": datetime.utcnow(),
                "media_urls": {"images": [], "video": None},
                "metrics": {
                    "likes": int(voteup_str) if voteup_str.isdigit() else 0,
                    "comments": 0,
                    "shares": 0,
                    "views": 0,
                },
            }
        except Exception as e:
            logger.error(f"Error parsing Zhihu article: {e}")
            return None
    
    def get_collected_data(self) -> List[dict]:
        return self.collected_data


async def load_account_cookies_by_platform(db, platform: str) -> tuple[list[dict], int]:
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
        return [], 0
    
    if not account:
        return [], 0
    
    try:
        cookies = json.loads(account.cookie_data)
        return cookies, account.id
    except:
        return [], 0
