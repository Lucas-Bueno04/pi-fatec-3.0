"""
=============================================================================
LABQUIZ ETEC — Testes unitários: AuthService (expandido)
=============================================================================
Cobre:
  - register: sucesso, email duplicado, LGPD não aceito
  - login: sucesso, senha errada, user não encontrado, usuário inativo
  - refresh: sucesso, user não encontrado, user inativo
  - get_profile: sucesso, não encontrado
  - _build_tokens: estrutura dos tokens
=============================================================================
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, LGPDConsentCreate
from app.models.user import User, UserRole, LGPDConsent, UserProgress
from app.security.password import hash_password
from app.security.jwt import create_refresh_token


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def auth_service(mock_db):
    return AuthService(mock_db)


def _make_user(uid="s001", role=UserRole.ALUNO, is_active=True):
    return User(
        _id=uid, name="Ana Silva",
        email=f"{uid}@etec.sp.gov.br",
        hashed_password=hash_password("senha@123"),
        role=role, class_name="1Q-A",
        lgpd_consent=LGPDConsent(accepted=True),
        progress=UserProgress(),
        is_active=is_active,
    )


def _create_data(email="novo@etec.sp.gov.br", role=UserRole.ALUNO,
                 class_name="1Q-B", guardian=None):
    return UserCreate(
        name="Novo Aluno",
        email=email,
        password="senha@123",
        role=role,
        class_name=class_name,
        lgpd_consent=LGPDConsentCreate(accepted=True, guardian_name=guardian),
    )


# ── register ──────────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_success(auth_service, sample_student):
    with (
        patch.object(auth_service.user_repo, "find_by_email", new_callable=AsyncMock, return_value=None),
        patch.object(auth_service.user_repo, "create_user", new_callable=AsyncMock, return_value=sample_student),
        patch.object(auth_service.audit_repo, "log_action", new_callable=AsyncMock),
    ):
        result = await auth_service.register(_create_data(), ip="127.0.0.1")
    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_lgpd_not_accepted_raises():
    """LGPD não aceita → ValidationError antes mesmo de chamar o service."""
    with pytest.raises(Exception):
        LGPDConsentCreate(accepted=False)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_email_already_exists(auth_service, sample_student):
    with patch.object(auth_service.user_repo, "find_by_email",
                      new_callable=AsyncMock, return_value=sample_student):
        with pytest.raises(HTTPException) as exc:
            await auth_service.register(
                _create_data(email=sample_student.email), ip="127.0.0.1"
            )
    assert exc.value.status_code == 400
    assert "já cadastrado" in exc.value.detail


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_com_guardian_name(auth_service, sample_student):
    """Registro com guardian_name (menor de idade) deve funcionar."""
    with (
        patch.object(auth_service.user_repo, "find_by_email", new_callable=AsyncMock, return_value=None),
        patch.object(auth_service.user_repo, "create_user", new_callable=AsyncMock, return_value=sample_student),
        patch.object(auth_service.audit_repo, "log_action", new_callable=AsyncMock),
    ):
        result = await auth_service.register(
            _create_data(guardian="Maria"), ip="10.0.0.1"
        )
    assert result.access_token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_professor_sem_turma(auth_service, sample_teacher):
    """Professor não precisa de class_name."""
    with (
        patch.object(auth_service.user_repo, "find_by_email", new_callable=AsyncMock, return_value=None),
        patch.object(auth_service.user_repo, "create_user", new_callable=AsyncMock, return_value=sample_teacher),
        patch.object(auth_service.audit_repo, "log_action", new_callable=AsyncMock),
    ):
        result = await auth_service.register(
            _create_data(role=UserRole.PROFESSOR, class_name=None), ip="127.0.0.1"
        )
    assert result.access_token


# ── login ─────────────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_success(auth_service, sample_student):
    with (
        patch.object(auth_service.user_repo, "find_by_email",
                     new_callable=AsyncMock, return_value=sample_student),
        patch.object(auth_service.audit_repo, "log_action", new_callable=AsyncMock),
    ):
        result = await auth_service.login(sample_student.email, "senha123", ip="127.0.0.1")
    assert result.access_token
    assert result.refresh_token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_wrong_password(auth_service, sample_student):
    with patch.object(auth_service.user_repo, "find_by_email",
                      new_callable=AsyncMock, return_value=sample_student):
        with pytest.raises(HTTPException) as exc:
            await auth_service.login(sample_student.email, "ERRADA", ip="127.0.0.1")
    assert exc.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_user_not_found(auth_service):
    with patch.object(auth_service.user_repo, "find_by_email",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await auth_service.login("ghost@etec.sp", "senha@123", ip="127.0.0.1")
    assert exc.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_usuario_inativo_retorna_403(auth_service):
    """Usuário inativo deve ser bloqueado com HTTP 403."""
    inativo = _make_user(is_active=False)
    with patch.object(auth_service.user_repo, "find_by_email",
                      new_callable=AsyncMock, return_value=inativo):
        with pytest.raises(HTTPException) as exc:
            await auth_service.login(inativo.email, "senha@123", ip="127.0.0.1")
    assert exc.value.status_code == 403


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_registra_audit_log(auth_service, sample_student):
    """Login bem-sucedido deve registrar audit log."""
    with (
        patch.object(auth_service.user_repo, "find_by_email",
                     new_callable=AsyncMock, return_value=sample_student),
        patch.object(auth_service.audit_repo, "log_action",
                     new_callable=AsyncMock) as mock_audit,
    ):
        await auth_service.login(sample_student.email, "senha123", ip="10.0.0.5")
    mock_audit.assert_called_once()
    call_arg = mock_audit.call_args[0][0]
    assert call_arg.action == "LOGIN"
    assert call_arg.ip_address == "10.0.0.5"


# ── refresh ───────────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_token_sucesso(auth_service, sample_student):
    """Refresh válido deve retornar novos tokens."""
    refresh_tok = create_refresh_token({
        "sub": sample_student.id, "role": sample_student.role.value,
        "email": sample_student.email,
    })
    with patch.object(auth_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=sample_student):
        result = await auth_service.refresh(refresh_tok)
    assert result.access_token
    assert result.refresh_token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_user_nao_encontrado(auth_service, sample_student):
    """Refresh com user inexistente → HTTP 401."""
    refresh_tok = create_refresh_token({
        "sub": sample_student.id, "role": "ALUNO",
        "email": sample_student.email,
    })
    with patch.object(auth_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await auth_service.refresh(refresh_tok)
    assert exc.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_user_inativo(auth_service, sample_student):
    """Refresh com user inativo → HTTP 401."""
    inativo = _make_user(is_active=False)
    refresh_tok = create_refresh_token({
        "sub": inativo.id, "role": "ALUNO", "email": inativo.email,
    })
    with patch.object(auth_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=inativo):
        with pytest.raises(HTTPException) as exc:
            await auth_service.refresh(refresh_tok)
    assert exc.value.status_code == 401


# ── get_profile ───────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_profile_sucesso(auth_service, sample_student):
    with patch.object(auth_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=sample_student):
        profile = await auth_service.get_profile(sample_student.id)
    assert profile.email == sample_student.email
    assert profile.role == UserRole.ALUNO


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_profile_nao_encontrado(auth_service):
    with patch.object(auth_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await auth_service.get_profile("ghost")
    assert exc.value.status_code == 404


# ── _build_tokens ─────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_build_tokens_estrutura(auth_service, sample_student):
    tokens = auth_service._build_tokens(sample_student)
    assert tokens.token_type == "bearer"
    assert "." in tokens.access_token   # JWT tem 3 partes separadas por .
    assert "." in tokens.refresh_token
    assert tokens.access_token != tokens.refresh_token
