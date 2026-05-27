from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from loguru import logger

from ..core.config import settings
from ..models.user import User, LGPDConsent, UserProgress
from ..models.audit import AuditLog
from ..repositories.user_repository import UserRepository
from ..repositories.audit_repository import AuditRepository
from ..schemas.user import UserCreate, UserResponse, TokenResponse
from ..security.password import hash_password, verify_password
from ..security.jwt import create_access_token, create_refresh_token, verify_token


class AuthService:
    def __init__(self, db):
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    async def register(self, data: UserCreate, ip: str) -> TokenResponse:
        existing = await self.user_repo.find_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail já cadastrado.",
            )

        user = User(
            name=data.name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
            class_name=data.class_name,
            lgpd_consent=LGPDConsent(
                accepted=True,
                accepted_at=datetime.utcnow(),
                ip_address=ip,
                guardian_name=data.lgpd_consent.guardian_name,
            ),
            progress=UserProgress(),
        )
        created = await self.user_repo.create_user(user)

        await self.audit_repo.log_action(AuditLog(
            user_id=created.id,
            action="REGISTER",
            resource="user",
            resource_id=created.id,
            ip_address=ip,
            details={"email": data.email, "role": data.role.value},
        ))

        logger.info(f"Novo usuário registrado: {created.email} ({created.role.value})")
        return self._build_tokens(created)

    async def login(self, email: str, password: str, ip: str) -> TokenResponse:
        user = await self.user_repo.find_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos.",
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo.")

        await self.audit_repo.log_action(AuditLog(
            user_id=user.id,
            action="LOGIN",
            resource="session",
            ip_address=ip,
            details={"email": email},
        ))

        return self._build_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        user = await self.user_repo.find_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")
        return self._build_tokens(user)

    def _build_tokens(self, user: User) -> TokenResponse:
        token_data = {"sub": user.id, "role": user.role.value, "email": user.email}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def get_profile(self, user_id: str) -> UserResponse:
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            class_name=user.class_name,
            is_active=user.is_active,
            progress=user.progress,
            created_at=user.created_at,
        )
