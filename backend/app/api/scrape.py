from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.models.database import PlatformEnum
from app.crud.content import upsert_content, upsert_content_batch
from app.services.scraper import PlatformScraper, load_account_cookies_by_platform
import re
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)
router = APIRouter()


class ScrapeInstantRequest(BaseModel):
    url: str


class ScrapeInstantResponse(BaseModel):
    success: bool
    message: str
    platform: Optional[str] = None
    platform_post_id: Optional[str] = None
    title: Optional[str] = None
    author_name: Optional[str] = None
    metrics: Optional[dict] = None
    count: Optional[int] = None


def clean_url(url: str, platform: str) -> str:
    parsed = urlparse(url)
    params_to_keep = []
    query_params = parse_qs(parsed.query)
    
    if platform == "xiaohongshu":
        if 'note' in query_params:
            params_to_keep.append(('note', query_params['note'][0]))
        if 'user_id' in query_params:
            params_to_keep.append(('user_id', query_params['user_id'][0]))
        for param in ['channel', 'xsec_source', 'xsec_token', 'xsecappid']:
            if param in query_params:
                del query_params[param]
    elif platform == "zhihu":
        if 'id' in query_params:
            params_to_keep.append(('id', query_params['id'][0]))
        for param in ['utm_source', 'utm_medium']:
            if param in query_params:
                del query_params[param]
    
    new_query = '&'.join(f"{k}={v}" for k, v in params_to_keep)
    clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if new_query:
        clean_url += f"?{new_query}"
    return clean_url


def parse_xhs_url(url: str) -> dict:
    from urllib.parse import unquote
    
    url = url.strip()
    
    if 'xhslink.com' in url or 'xhs.cn' in url:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        target_url = None
        for param in ['target', 'url', 'redirect', 'u']:
            if param in query_params:
                target_url = query_params[param][0]
                break
        
        if target_url and ('xiaohongshu' in target_url or 'xhs.cn' in target_url):
            url = unquote(target_url)
        elif target_url:
            return {
                "platform": "xiaohongshu",
                "type": "short_url",
                "id": url
            }
    
    if not url.startswith('http://') and not url.startswith('https://'):
        extracted_urls = re.findall(r'https?://[^\s]+', url)
        if extracted_urls:
            url = extracted_urls[0]
    
    url = clean_url(url, "xiaohongshu")
    
    note_patterns = [
        r'xiaohongshu\.com/discovery/item/(\w+)',
        r'xiaohongshu\.com/discovery/(\w+)',
        r'xiaohongshu\.com/explore/(\w+)',
        r'xiaohongshu\.com/detail/(\w+)',
        r'xiaohongshu\.com/express/(\w+)',
        r'xiaohongshu\.com/.*?note=(\w+)',
    ]
    
    author_patterns = [
        r'xiaohongshu\.com/user/profile/(\w+)',
        r'xiaohongshu\.com/.*?user_id=(\w+)',
    ]
    
    for pattern in note_patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "platform": "xiaohongshu",
                "type": "note",
                "id": match.group(1) if match.lastindex else match.group(0)
            }
    
    for pattern in author_patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "platform": "xiaohongshu",
                "type": "author",
                "id": match.group(1) if match.lastindex else match.group(0)
            }
    
    if 'xhslink.com' in url or 'xhs.cn' in url:
        return {
            "platform": "xiaohongshu",
            "type": "unknown",
            "id": url
        }
    
    raise ValueError(f"Unable to parse XHS URL: {url}")


def parse_zhihu_url(url: str) -> dict:
    from urllib.parse import unquote
    
    url = url.strip()
    
    if not url.startswith('http://') and not url.startswith('https://'):
        extracted_urls = re.findall(r'https?://[^\s]+', url)
        if extracted_urls:
            url = extracted_urls[0]
    
    url = clean_url(url, "zhihu")
    
    article_patterns = [
        r'zhihu\.com/answer/(\d+)',
        r'zhihu\.com/api/v4/articles/(\d+)',
        r'zhihu\.com/p/(\d+)',
        r'zhihu\.com/question/\d+/answer/(\d+)',
        r'zhihu\.com/zhuanlan/([a-zA-Z0-9_-]+)/(\d+)',
        r'zhihu\.com/.*?id=(\d+)',
    ]
    
    author_patterns = [
        r'zhihu\.com/people/(\w+)',
        r'zhihu\.com/.*?people/(\w+)',
    ]
    
    for pattern in article_patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "platform": "zhihu",
                "type": "article",
                "id": match.group(1) if match.lastindex else match.group(0)
            }
    
    for pattern in author_patterns:
        match = re.search(pattern, url)
        if match:
            return {
                "platform": "zhihu",
                "type": "author",
                "id": match.group(1) if match.lastindex else match.group(0)
            }
    
    raise ValueError(f"Unable to parse Zhihu URL: {url}")


def parse_url(url: str) -> dict:
    url = url.strip()
    
    url_lower = url.lower()
    
    if 'xiaohongshu' in url_lower or 'xhs.cn' in url_lower or 'xhslink.com' in url_lower:
        return parse_xhs_url(url)
    elif 'zhihu' in url_lower:
        return parse_zhihu_url(url)
    
    extracted_urls = re.findall(r'https?://[^\s]+', url)
    if extracted_urls:
        url = extracted_urls[0]
        url_lower = url.lower()
        
        if 'xiaohongshu' in url_lower or 'xhs.cn' in url_lower or 'xhslink.com' in url_lower:
            return parse_xhs_url(url)
        elif 'zhihu' in url_lower:
            return parse_zhihu_url(url)
    
    raise ValueError(f"Unsupported platform. URL must contain 'xiaohongshu' or 'zhihu'")


@router.post("/instant", response_model=ScrapeInstantResponse)
async def scrape_instant(
    request: ScrapeInstantRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        parsed = parse_url(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    platform = parsed["platform"]
    cookies, account_id = await load_account_cookies_by_platform(db, platform)
    
    async with PlatformScraper(cookies, account_id=account_id, db=db) as scraper:
        try:
            if platform == "xiaohongshu":
                if parsed["type"] == "note":
                    result = await scraper.scrape_xhs_note(parsed["id"])
                    
                    if not result:
                        raise HTTPException(status_code=404, detail="Note not found or content unavailable")
                    
                    result["publish_date"] = result.get("publish_date")
                    
                    content, is_new = await upsert_content(
                        db, PlatformEnum.XHS, result["platform_post_id"], result
                    )
                    
                    return ScrapeInstantResponse(
                        success=True,
                        message="Note scraped successfully",
                        platform="xiaohongshu",
                        platform_post_id=result["platform_post_id"],
                        title=result.get("title"),
                        author_name=result.get("author_name"),
                        metrics=result.get("metrics"),
                    )
                
                elif parsed["type"] == "short_url":
                    result = await scraper.scrape_xhs_from_short_url(parsed["id"])
                    
                    if not result:
                        raise HTTPException(status_code=404, detail="Could not resolve short URL")
                    
                    content, is_new = await upsert_content(
                        db, PlatformEnum.XHS, result["platform_post_id"], result
                    )
                    
                    return ScrapeInstantResponse(
                        success=True,
                        message="Note scraped successfully from short URL",
                        platform="xiaohongshu",
                        platform_post_id=result["platform_post_id"],
                        title=result.get("title"),
                        author_name=result.get("author_name"),
                        metrics=result.get("metrics"),
                    )
                
                elif parsed["type"] == "author":
                    results = await scraper.scrape_xhs_author(parsed["id"], depth=1)
                    
                    if not results:
                        raise HTTPException(status_code=404, detail="No posts found for this author")
                    
                    inserted, updated = await upsert_content_batch(db, PlatformEnum.XHS, results)
                    
                    return ScrapeInstantResponse(
                        success=True,
                        message=f"Scraped {len(results)} posts (new: {inserted}, updated: {updated})",
                        platform="xiaohongshu",
                        count=len(results),
                    )
            
            elif platform == "zhihu":
                if parsed["type"] == "article":
                    result = await scraper.scrape_zhihu_article(parsed["id"])
                    
                    if not result:
                        raise HTTPException(status_code=404, detail="Article not found or content unavailable")
                    
                    content, is_new = await upsert_content(
                        db, PlatformEnum.ZHIHU, result["platform_post_id"], result
                    )
                    
                    return ScrapeInstantResponse(
                        success=True,
                        message="Article scraped successfully",
                        platform="zhihu",
                        platform_post_id=result["platform_post_id"],
                        title=result.get("title"),
                        author_name=result.get("author_name"),
                        metrics=result.get("metrics"),
                    )
                    
                elif parsed["type"] == "author":
                    results = await scraper.scrape_zhihu_author(parsed["id"], depth=1)
                    
                    if not results:
                        raise HTTPException(status_code=404, detail="No articles found for this author")
                    
                    inserted, updated = await upsert_content_batch(db, PlatformEnum.ZHIHU, results)
                    
                    return ScrapeInstantResponse(
                        success=True,
                        message=f"Scraped {len(results)} articles (new: {inserted}, updated: {updated})",
                        platform="zhihu",
                        count=len(results),
                    )
            
            raise HTTPException(status_code=400, detail="Unsupported URL type")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
