from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.database import PlatformAccount, AccountStatusEnum, PlatformEnum
from app.services.xhs_login import XHSLoginService
from app.services.redis_session import QRLoginSession
import uuid
import json

router = APIRouter(prefix="/accounts/xhs", tags=["xhs-auth"])


@router.post("/qr")
async def generate_qr():
    session_id = str(uuid.uuid4())
    service = XHSLoginService()
    
    try:
        result = await service.generate_qr(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{session_id}")
async def check_login_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    session = QRLoginSession(session_id)
    
    if not await session.exists():
        return {"session_id": session_id, "status": "expired", "message": "Session not found or expired"}
    
    status_data = await session.get_status()
    
    if status_data["status"] == "success":
        cookies = status_data.get("cookies")
        if cookies:
            try:
                cookies_json = json.loads(cookies)
                
                account = PlatformAccount(
                    platform_name=PlatformEnum.XHS,
                    account_name=f"xhs_{session_id[:8]}",
                    cookie_data=json.dumps(cookies_json),
                    status=AccountStatusEnum.ACTIVE,
                )
                db.add(account)
                await db.commit()
                await db.refresh(account)
                
                await session.delete()
                
                return {
                    "session_id": session_id,
                    "status": "success",
                    "account_id": account.id,
                }
            except Exception as e:
                return {
                    "session_id": session_id,
                    "status": "error",
                    "message": f"Failed to save account: {str(e)}"
                }
    
    return status_data


@router.post("/cleanup")
async def cleanup_sessions():
    from app.services.redis_session import get_redis
    client = await get_redis()
    keys = []
    async for key in client.scan_iter("qr_session:*"):
        keys.append(key)
    if keys:
        await client.delete(*keys)
    return {"deleted": len(keys)}
