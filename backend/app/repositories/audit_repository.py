from typing import List, Optional
from .base import BaseRepository
from ..models.audit import AuditLog


class AuditRepository(BaseRepository[AuditLog]):
    collection_name = "audit_logs"
    model_class = AuditLog

    async def log_action(self, log: AuditLog) -> AuditLog:
        return await self.create(log.to_mongo())

    async def find_by_user(self, user_id: str, limit: int = 50) -> List[AuditLog]:
        return await self.find_many(
            {"user_id": user_id},
            limit=limit,
            sort=[("timestamp", -1)],
        )

    async def find_by_resource(self, resource: str, resource_id: Optional[str] = None) -> List[AuditLog]:
        f = {"resource": resource}
        if resource_id:
            f["resource_id"] = resource_id
        return await self.find_many(f, limit=100, sort=[("timestamp", -1)])
