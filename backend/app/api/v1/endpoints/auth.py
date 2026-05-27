from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from ....core.database import get_database
from ....schemas.user import UserCreate, UserResponse, TokenResponse, RefreshTokenRequest, UserUpdate
from ....services.auth_service import AuthService
from ....security.jwt import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _get_ip(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, request: Request, db=Depends(get_database)):
    """Cadastro de novo usuário com consentimento LGPD obrigatório."""
    service = AuthService(db)
    return await service.register(data, _get_ip(request))


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db=Depends(get_database)):
    """Login com e-mail e senha. Retorna tokens JWT."""
    service = AuthService(db)
    return await service.login(form_data.username, form_data.password, _get_ip(request))


@router.post("/login/json", response_model=TokenResponse)
async def login_json(data: dict, request: Request, db=Depends(get_database)):
    """Login via JSON (para aplicações mobile/desktop)."""
    service = AuthService(db)
    return await service.login(data["email"], data["password"], _get_ip(request))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db=Depends(get_database)):
    """Renovação do access token usando refresh token."""
    service = AuthService(db)
    return await service.refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_active_user)):
    """Retorna dados do usuário autenticado."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        class_name=current_user.class_name,
        is_active=current_user.is_active,
        progress=current_user.progress,
        created_at=current_user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user=Depends(get_current_active_user), db=Depends(get_database)):
    """Atualiza dados do perfil do usuário autenticado."""
    from ....repositories.user_repository import UserRepository
    repo = UserRepository(db)
    updated = await repo.update_user(current_user.id, data.model_dump(exclude_none=True))
    return UserResponse(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        role=updated.role,
        class_name=updated.class_name,
        is_active=updated.is_active,
        progress=updated.progress,
        created_at=updated.created_at,
    )
