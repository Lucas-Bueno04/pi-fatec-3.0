from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from loguru import logger
from jose import JWTError, jwt
from ..core.config import settings


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        user_id = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                token = auth.split(" ", 1)[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("sub")
            except JWTError:
                pass

        response = await call_next(request)

        ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} "
            f"[user={user_id or 'anon'}] [ip={ip}]"
        )

        return response
