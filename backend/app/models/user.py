from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


class UserRole(str, Enum):
    ALUNO = "ALUNO"
    PROFESSOR = "PROFESSOR"
    ADMINISTRADOR = "ADMINISTRADOR"


class LGPDConsent(BaseModel):
    accepted: bool = False
    accepted_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    guardian_name: Optional[str] = None  # required for minors


class UserProgress(BaseModel):
    facil_unlocked: bool = True
    medio_unlocked: bool = False
    dificil_unlocked: bool = False
    facil_best_accuracy: float = 0.0
    medio_best_accuracy: float = 0.0
    dificil_best_accuracy: float = 0.0


class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    email: EmailStr
    hashed_password: str
    role: UserRole = UserRole.ALUNO
    is_active: bool = True
    class_name: Optional[str] = None
    lgpd_consent: LGPDConsent = Field(default_factory=LGPDConsent)
    progress: UserProgress = Field(default_factory=UserProgress)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True, "arbitrary_types_allowed": True}

    def to_mongo(self) -> Dict[str, Any]:
        data = self.model_dump(exclude={"id"}, by_alias=False)
        data["lgpd_consent"] = self.lgpd_consent.model_dump()
        data["progress"] = self.progress.model_dump()
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "User":
        if data and "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
