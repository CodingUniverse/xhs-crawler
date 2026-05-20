import asyncio
import json
import random
import re
from typing import Optional, List, Dict
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
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

MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
]


class PlatformScraper:

    def __init__(self, cookies: Optional[List[dict]] = None, proxy: Optional[str] = None,
                 account_id: Optional[int] = None, db=None, xsec_params: Optional[dict] = None):
        self.cookies = cookies or []
        self.proxy = proxy
        self.account_id = account_id
        self.db = db
        self.xsec_params = xsec_params or {}
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.collected_data: List[dict] = []
        self._consecutive_failures = 0

    async def _create_browser(self, use_mobile_ua: bool = False):
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1280,720",
            ]
        )

        ua = random.choice(MOBILE_USER_AGENTS if use_mobile_ua else DESKTOP_USER_AGENTS)

        context_options = {
            "viewport": {"width": 390, "height": 844} if use_mobile_ua else {"width": 1280, "height": 720},
            "user_agent": ua,
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

    async def __aenter__(self):
        return await self._create_browser(use_mobile_ua=False)

    async def _trigger_circuit_breaker(self):
        if self.account_id and self.db:
            try:
                from sqlalchemy import update
                from app.models.database import PlatformAccount, AccountStatusEnum

                stmt = update(PlatformAccount).where(
                    PlatformAccount.id == self.account_id
                ).values(status=AccountStatusEnum.EXPIRED)

                await self.db.execute(stmt)
                await self.db.commit()

                logger.warning(f"账号异常，触发反爬，已标记为过期 (account_id: {self.account_id})")
            except Exception as e:
                logger.error(f"Failed to mark account as expired: {e}")

    async def _check_and_circuit_break(self, html: str, url: str = "") -> bool:
        is_login_redirect = '/login' in url or 'redirectPath=' in url
        is_captcha = 'captcha' in html.lower() or '验证' in html
        is_blocked = '当前笔记暂时无法浏览' in html or 'error_code=300031' in html

        if is_login_redirect or is_captcha or is_blocked:
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
        for obj in [self.page, self.context, self.browser]:
            if obj:
                try:
                    await obj.close()
                except:
                    pass

    async def _resolve_xhs_short_url(self, short_url: str) -> Optional[dict]:
        logger.info(f"Resolving XHS short URL: {short_url}")

        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                       "--disable-gpu", "--single-process",
                       "--disable-blink-features=AutomationControlled"]
            )
            ua = random.choice(MOBILE_USER_AGENTS)
            ctx = await browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent=ua,
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )

            for cookie in self.cookies:
                try:
                    await ctx.add_cookies([cookie])
                except:
                    pass

            page = await ctx.new_page()

            await page.goto(short_url, wait_until="domcontentloaded", timeout=30000)

            resolved_url = page.url
            for _ in range(15):
                if 'xiaohongshu.com/explore/' in page.url or 'xiaohongshu.com/discovery/item/' in page.url:
                    resolved_url = page.url
                    break
                await asyncio.sleep(1)

            logger.info(f"Resolved to: {resolved_url}")

            result = {"resolved_url": resolved_url}

            note_match = re.search(r'/(?:explore|discovery/item)/([a-zA-Z0-9]+)', resolved_url)
            if note_match:
                result["note_id"] = note_match.group(1)

            query_params = parse_qs(urlparse(resolved_url).query)
            if 'xsec_token' in query_params:
                result["xsec_token"] = query_params['xsec_token'][0]
            if 'xsec_source' in query_params:
                result["xsec_source"] = query_params['xsec_source'][0]

            await ctx.close()
            await browser.close()
            await pw.stop()

            return result if result.get("note_id") else None

        except Exception as e:
            logger.error(f"Failed to resolve XHS short URL {short_url}: {e}")
            return None

    async def _call_xhs_note_api(self, note_id: str) -> Optional[dict]:
        api_url = f"https://edith.xiaohongshu.com/api/sns/h5/v1/note_info?note_id={note_id}"

        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                       "--disable-gpu", "--single-process",
                       "--disable-blink-features=AutomationControlled"]
            )
            ctx = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=random.choice(DESKTOP_USER_AGENTS),
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )

            for cookie in self.cookies:
                try:
                    await ctx.add_cookies([cookie])
                except:
                    pass

            page = await ctx.new_page()

            api_result = {}
            async def handle_response(response):
                if 'note_info' in response.url and response.status == 200:
                    try:
                        body = await response.json()
                        if body.get("success"):
                            api_result["data"] = body.get("data", {})
                            api_result["raw"] = body
                    except:
                        pass

            page.on("response", handle_response)

            await page.goto(api_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            await ctx.close()
            await browser.close()
            await pw.stop()

            if api_result.get("data"):
                return api_result["data"]
            return None

        except Exception as e:
            logger.error(f"XHS note API failed for {note_id}: {e}")
            return None

    async def scrape_xhs_note(self, note_id_or_url: str) -> Optional[dict]:
        is_short_url = 'xhslink.com' in note_id_or_url or '/o/' in note_id_or_url

        if is_short_url:
            resolved = await self._resolve_xhs_short_url(note_id_or_url)
            if not resolved:
                raise ValueError("无法解析小红书短链接")

            note_id = resolved["note_id"]
            if resolved.get("xsec_token") and "xsec_token" not in self.xsec_params:
                self.xsec_params["xsec_token"] = resolved["xsec_token"]
            if resolved.get("xsec_source") and "xsec_source" not in self.xsec_params:
                self.xsec_params["xsec_source"] = resolved["xsec_source"]
        else:
            note_id = note_id_or_url

        try:
            api_data = await self._call_xhs_note_api(note_id)
            if api_data:
                logger.info(f"API success for note {note_id}")
                return self._parse_api_note_data(api_data, note_id)
        except Exception as e:
            logger.warning(f"API failed for note {note_id}, falling back to HTML: {e}")

        target_url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if self.xsec_params:
            target_url += "?" + urlencode(self.xsec_params)

        logger.info(f"Falling back to HTML parse: {target_url}")

        try:
            await self._random_sleep()
            await self.page.goto(target_url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(2)

            current_url = self.page.url
            logger.info(f"HTML page URL: {current_url}")

            if '/login' in current_url or 'redirectPath=' in current_url:
                raise ValueError(f"笔记 {note_id} 需要登录才能查看，请添加有效Cookie")

            html_content = await self.page.content()

            if await self._check_and_circuit_break(html_content, current_url):
                if '当前笔记暂时无法浏览' in html_content or 'error_code=300031' in html_content:
                    raise ValueError(f"笔记 {note_id} 暂时无法浏览，可能已被删除或设置权限")
                raise ValueError(f"笔记 {note_id} 被登录页/验证码拦截")

            state_match = re.search(r'__INITIAL_STATE__\s*=\s*({.*?});?\s*</script>', html_content, re.DOTALL)

            if not state_match:
                raise ValueError(f"笔记 {note_id}：未找到初始状态，页面结构可能已变更")

            json_str = state_match.group(1)
            json_str = re.sub(r':undefined([,}])', r':null\1', json_str)

            try:
                state_data = json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON 解析失败: {e}")

            target_note = None

            note_data = state_data.get("noteData", {}).get("data", {}).get("noteData", {})
            if note_data and note_data.get("noteId") == note_id:
                target_note = note_data

            if not target_note and "note" in state_data and "noteDetailMap" in state_data.get("note", {}):
                note_detail_map = state_data["note"]["noteDetailMap"]
                for key in note_detail_map:
                    entry = note_detail_map[key]
                    nd = entry.get("note", entry)
                    if nd.get("note_id") == note_id or note_id in nd.get("note_id", ""):
                        target_note = nd
                        break
                if not target_note:
                    first_key = list(note_detail_map.keys())[0]
                    target_note = note_detail_map[first_key].get("note", note_detail_map[first_key])

            if not target_note:
                if "note" in state_data and "note" in state_data.get("note", {}):
                    target_note = state_data["note"]["note"]

            if not target_note:
                raise ValueError(f"数据错位，未能匹配到目标笔记 note_id={note_id}")

            return self._parse_note_data(target_note, note_id, current_url)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error scraping XHS note {note_id}: {e}")

        return None

    def _parse_note_data(self, note_data: dict, note_id: str, source_url: str) -> dict:
        title = note_data.get("title", "") or note_data.get("desc", "")[:100] or note_data.get("display_title", "")
        content_text = note_data.get("desc", "") or note_data.get("content", "")

        user_info = note_data.get("user", {}) or {}
        author_name = user_info.get("nickname", "") or user_info.get("nickName", "") or user_info.get("name", "")
        author_id = str(user_info.get("user_id", "") or user_info.get("userId", "") or "")

        interact_info = note_data.get("interact_info", {}) or note_data.get("interactInfo", {})
        likes = int(interact_info.get("liked_count", 0) or interact_info.get("likedCount", 0) or 0)
        comments = int(interact_info.get("comment_count", 0) or interact_info.get("commentCount", 0) or 0)
        shares = int(interact_info.get("share_count", 0) or interact_info.get("shareCount", 0) or 0)
        views = int(interact_info.get("play_count", 0) or interact_info.get("viewCount", 0) or 0)

        images = []
        image_list = note_data.get("image_list", []) or note_data.get("imageList", [])
        for img in image_list:
            if isinstance(img, str) and img.startswith("http"):
                images.append(img)
            elif isinstance(img, dict):
                url = None
                info_list = img.get("info_list", []) or img.get("infoList", [])
                if info_list:
                    scs = info_list[0].get("image_scs", {}) or info_list[0].get("imageScs", {})
                    url = scs.get("url_default", "") or scs.get("url", "") or info_list[0].get("url", "")
                if not url:
                    url = img.get("url_default", "") or img.get("url", "")
                if url and url.startswith("http") and url not in images:
                    images.append(url)

        publish_date = datetime.utcnow()
        ts = note_data.get("time", 0) or note_data.get("lastUpdateTime", 0)
        if ts:
            try:
                publish_date = datetime.fromtimestamp(ts / 1000)
            except:
                pass

        return {
            "platform_post_id": note_id,
            "source_url": source_url,
            "title": title,
            "content_text": content_text,
            "author_name": author_name,
            "author_id": author_id,
            "publish_date": publish_date,
            "media_urls": {"images": images, "video": None},
            "metrics": {
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "views": views,
            },
        }

    def _parse_api_note_data(self, api_data: dict, note_id: str) -> dict:
        items = api_data.get("items", [api_data])
        note = items[0] if items else api_data

        title = note.get("title", "") or note.get("display_title", "")
        content_text = note.get("desc", "") or note.get("content", "") or note.get("display_content", "")

        user = note.get("user", {}) or note.get("author", {})
        author_name = user.get("nickname", "") or user.get("name", "") or note.get("author_name", "")
        author_id = str(user.get("user_id", "") or note.get("author_id", "") or "")

        interact = note.get("interact_info", {}) or note.get("interactInfo", {})
        likes = int(interact.get("liked_count", 0) or interact.get("likeCount", 0) or 0)
        comments = int(interact.get("comment_count", 0) or interact.get("commentCount", 0) or 0)
        shares = int(interact.get("share_count", 0) or interact.get("shareCount", 0) or 0)
        views = int(interact.get("play_count", 0) or interact.get("viewCount", 0) or 0)

        images = []
        image_list = note.get("image_list", []) or note.get("images", []) or note.get("media", [])
        for img in image_list:
            if isinstance(img, str) and img.startswith("http"):
                images.append(img)
            elif isinstance(img, dict):
                url = img.get("url_default", "") or img.get("url", "") or img.get("original", "") or \
                      img.get("info_list", [{}])[0].get("image_scs", {}).get("url_default", "")
                if url and url.startswith("http"):
                    images.append(url)

        return {
            "platform_post_id": note_id,
            "source_url": f"https://www.xiaohongshu.com/explore/{note_id}",
            "title": title,
            "content_text": content_text,
            "author_name": author_name,
            "author_id": author_id,
            "publish_date": datetime.utcnow(),
            "media_urls": {"images": images, "video": None},
            "metrics": {"likes": likes, "comments": comments, "shares": shares, "views": views},
        }

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
                    nid = note.get("note_id")
                    if nid:
                        parsed = self._parse_xhs_note_data(note, nid)
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

            nid = str(note.get("note_id") or note_id or "")
            if not nid:
                return None

            user = note.get("user") or {}
            interact_info = note.get("interact_info") or note.get("interactInfo") or {}
            image_list = note.get("image_list") or note.get("imageList") or []

            title = note.get("title", "") or data.get("title", "")
            desc = note.get("desc", "") or note.get("content", "") or data.get("display_content", "") or data.get("desc", "")

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
                    elif isinstance(img.get("url"), str) and img["url"].startswith("http"):
                        images.append(img["url"])

            def parse_number(val):
                if not val:
                    return 0
                try:
                    return int(str(val).replace(",", ""))
                except:
                    return 0

            return {
                "platform_post_id": nid,
                "title": title or (desc[:100] if desc else f"笔记 {nid}"),
                "content_text": desc,
                "author_name": user.get("nickname", "") or user.get("nickName", "") or data.get("author", ""),
                "author_id": str(user.get("user_id", "") or user.get("userId", "") or data.get("author_id", "")),
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
                "content_text": "页面被拦截或需登录才能查看内容。请在账户管理中添加已登录的知乎Cookie后再试。" if is_blocked else "无法提取页面内容，可能是反爬措施或页面结构变化。",
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
