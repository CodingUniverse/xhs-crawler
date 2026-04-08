import json
from typing import Optional, Dict
from app.core.config import get_settings

settings = get_settings()

in_memory_sessions: Dict[str, dict] = {}
redis_client = None
use_redis = False


async def get_redis():
    global redis_client, use_redis
    if redis_client is None:
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await redis_client.ping()
            use_redis = True
        except Exception:
            use_redis = False
            redis_client = None
    return redis_client


class QRLoginSession:
    SESSION_EXPIRE = 180
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.key = f"qr_session:{session_id}"
    
    async def create(self, page_data: dict) -> None:
        if use_redis and redis_client:
            await redis_client.setex(
                self.key,
                self.SESSION_EXPIRE,
                json.dumps(page_data)
            )
        else:
            in_memory_sessions[self.key] = page_data
    
    async def get(self) -> Optional[dict]:
        if use_redis and redis_client:
            data = await redis_client.get(self.key)
            if data:
                return json.loads(data)
            return None
        else:
            return in_memory_sessions.get(self.key)
    
    async def update(self, page_data: dict) -> None:
        if use_redis and redis_client:
            await redis_client.setex(
                self.key,
                self.SESSION_EXPIRE,
                json.dumps(page_data)
            )
        else:
            in_memory_sessions[self.key] = page_data
    
    async def delete(self) -> None:
        if use_redis and redis_client:
            await redis_client.delete(self.key)
        else:
            in_memory_sessions.pop(self.key, None)
    
    async def exists(self) -> bool:
        if use_redis and redis_client:
            return await redis_client.exists(self.key) > 0
        else:
            return self.key in in_memory_sessions
    
    async def set_status(self, status: str, cookies: Optional[dict] = None, account_id: Optional[int] = None, message: Optional[str] = None) -> None:
        data = await self.get() or {}
        data["status"] = status
        if cookies:
            data["cookies"] = cookies
        if account_id:
            data["account_id"] = account_id
        if message:
            data["message"] = message
        
        if use_redis and redis_client:
            await redis_client.setex(self.key, self.SESSION_EXPIRE, json.dumps(data))
        else:
            in_memory_sessions[self.key] = data
    
    async def get_status(self) -> dict:
        data = await self.get()
        if not data:
            return {"status": "expired", "session_id": self.session_id}
        return {
            "session_id": self.session_id,
            "status": data.get("status", "pending"),
            "cookies": data.get("cookies"),
            "account_id": data.get("account_id"),
            "message": data.get("message"),
        }
