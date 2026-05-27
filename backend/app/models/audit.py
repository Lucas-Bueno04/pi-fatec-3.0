from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        return self.model_dump(exclude={"id"}, by_alias=False)

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "AuditLog":
        if data and "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
