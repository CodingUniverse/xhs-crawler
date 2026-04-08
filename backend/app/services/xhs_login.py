import asyncio
import base64
import uuid
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright
from app.services.redis_session import QRLoginSession
import json

browser_instance: Optional[Browser] = None
playwright_instance: Optional[Playwright] = None


async def get_playwright() -> Playwright:
    global playwright_instance
    if playwright_instance is None:
        playwright_instance = await async_playwright().start()
    return playwright_instance


async def get_browser() -> Browser:
    global browser_instance
    pw = await get_playwright()
    if browser_instance is None or not browser_instance.is_connected():
        browser_instance = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--window-size=1280,720",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-sync",
                "--disable-translate",
                "--metrics-recording-only",
                "--mute-audio",
                "--no-first-run",
            ]
        )
    return browser_instance


async def close_browser() -> None:
    global browser_instance
    if browser_instance:
        await browser_instance.close()
        browser_instance = None


async def close_playwright() -> None:
    global playwright_instance
    if playwright_instance:
        await playwright_instance.stop()
        playwright_instance = None


class XHSLoginService:
    QR_PAGE_URL = "https://www.xiaohongshu.com/explore"
    QR_SELECTOR = ".qrcode, .login-qrcode, [class*='qrcode'], .qr-code"
    LOGIN_SUCCESS_SELECTORS = [
        ".user-info",
        "[class*='user'] [class*='avatar']",
        ".profile-avatar",
        "a[href*='creator']",
        "[class*='logged']",
        "[class*='avatar']",
        ".user-name",
    ]
    
    async def generate_qr(self, session_id: str) -> dict:
        browser = await get_browser()
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        session = QRLoginSession(session_id)
        
        try:
            await page.goto(self.QR_PAGE_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
            
            qr_selector = self.QR_SELECTOR
            qr_element = await page.query_selector(qr_selector)
            
            if qr_element:
                qr_canvas = await page.query_selector(f"{qr_selector} canvas")
                if qr_canvas:
                    screenshot = await qr_canvas.screenshot()
                    qr_base64 = base64.b64encode(screenshot).decode()
                else:
                    qr_img = await qr_element.query_selector("img")
                    if qr_img:
                        qr_src = await qr_img.get_attribute("src")
                        if qr_src and qr_src.startswith("data:image"):
                            qr_base64 = qr_src.split(",")[1]
                        else:
                            screenshot = await qr_element.screenshot()
                            qr_base64 = base64.b64encode(screenshot).decode()
                    else:
                        screenshot = await qr_element.screenshot()
                        qr_base64 = base64.b64encode(screenshot).decode()
            else:
                screenshot = await page.screenshot()
                qr_base64 = base64.b64encode(screenshot).decode()
            
            await session.create({
                "context_id": str(id(context)),
                "page_url": page.url,
                "status": "pending",
            })
            
            asyncio.create_task(self._poll_login_status(page, session))
            
            return {
                "qr_code": qr_base64,
                "session_id": session_id,
                "status": "pending"
            }
            
        except Exception as e:
            await context.close()
            await session.set_status("error", message=str(e))
            raise
    
    async def _poll_login_status(self, page: Page, session: QRLoginSession) -> None:
        try:
            for _ in range(90):
                await asyncio.sleep(2)
                
                if not page.is_closed():
                    current_url = page.url
                    
                    for selector in self.LOGIN_SUCCESS_SELECTORS:
                        if await page.query_selector(selector):
                            cookies = await page.context.cookies()
                            await session.set_status("success", cookies=json.dumps(cookies))
                            await page.context.close()
                            return
                    
                    if "creator.xiaohongshu.com" in current_url and "login" not in current_url:
                        cookies = await page.context.cookies()
                        await session.set_status("success", cookies=json.dumps(cookies))
                        await page.context.close()
                        return
                else:
                    break
            
            await session.set_status("timeout")
            if not page.is_closed():
                await page.context.close()
                
        except Exception as e:
            await session.set_status("error", message=str(e))
            if not page.is_closed():
                await page.context.close()
    
    async def get_login_status(self, session_id: str) -> dict:
        session = QRLoginSession(session_id)
        return await session.get_status()
