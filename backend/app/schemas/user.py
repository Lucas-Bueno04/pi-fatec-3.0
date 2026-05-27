from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from ..models.user import UserRole, UserProgress, LGPDConsent


class LGPDConsentCreate(BaseModel):
    accepted: bool
    guardian_name: Optional[str] = None

    @field_validator("accepted")
    @classmethod
    def must_be_accepted(cls, v):
        if not v:
            raise ValueError("O consentimento LGPD é obrigatório para utilizar o sistema.")
        return v


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.ALUNO
    class_name: Optional[str] = None
    lgpd_consent: LGPDConsentCreate

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("A senha deve ter no mínimo 8 caracteres.")
        return v

    @model_validator(mode="after")
    def class_required_for_student(self):
        if self.role == UserRole.ALUNO and not self.class_name:
            raise ValueError("Alunos devem informar a turma.")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    class_name: Optional[str] = None
    is_active: bool
    progress: UserProgress
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = None
    is_active: Optional[bool] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
