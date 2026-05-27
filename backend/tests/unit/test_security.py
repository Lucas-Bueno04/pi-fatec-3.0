"""
=============================================================================
LABQUIZ ETEC — Testes unitários: Segurança (JWT + Password)
=============================================================================
Cobre:
  - hash_password / verify_password
  - create_access_token / create_refresh_token
  - verify_token (access, refresh, adulterado, expirado, tipo errado)
  - get_current_user (válido, inexistente, inativo)
  - require_role (papel correto, papel incorreto)
=============================================================================
"""
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.security.password import hash_password, verify_password
from app.security.jwt import (
    create_access_token, create_refresh_token, verify_token,
)
from app.models.user import UserRole


# ── Password ──────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_hash_password_retorna_string_diferente():
    """Hash não deve ser igual à senha em texto puro."""
    plain = "minhaSenha@123"
    hashed = hash_password(plain)
    assert hashed != plain


@pytest.mark.unit
def test_hash_password_bcrypt_prefix():
    """Hash bcrypt deve iniciar com $2b$ ou $2y$."""
    hashed = hash_password("qualquerCoisa")
    assert hashed.startswith("$2")


@pytest.mark.unit
def test_verify_password_correta():
    """verify_password retorna True para senha correta."""
    plain = "Senha@123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


@pytest.mark.unit
def test_verify_password_errada():
    """verify_password retorna False para senha incorreta."""
    hashed = hash_password("correta")
    assert verify_password("errada", hashed) is False


@pytest.mark.unit
def test_verify_password_vazia_falha():
    """Senha vazia não deve verificar."""
    hashed = hash_password("senha_real")
    assert verify_password("", hashed) is False


@pytest.mark.unit
def test_dois_hashes_da_mesma_senha_sao_diferentes():
    """bcrypt gera salt aleatório — dois hashes nunca são iguais."""
    plain = "senha_igual"
    h1 = hash_password(plain)
    h2 = hash_password(plain)
    assert h1 != h2
    assert verify_password(plain, h1)
    assert verify_password(plain, h2)


# ── JWT – access token ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_create_access_token_retorna_string():
    """create_access_token deve retornar uma string não-vazia."""
    token = create_access_token({"sub": "user1", "role": "ALUNO"})
    assert isinstance(token, str)
    assert len(token) > 20


@pytest.mark.unit
def test_create_access_token_payload_correto():
    """Payload do access token deve conter sub, role e type=access."""
    token = create_access_token({"sub": "u1", "role": "PROFESSOR"})
    payload = verify_token(token, token_type="access")
    assert payload["sub"] == "u1"
    assert payload["role"] == "PROFESSOR"
    assert payload["type"] == "access"


@pytest.mark.unit
def test_create_refresh_token_type_refresh():
    """Payload do refresh token deve ter type=refresh."""
    token = create_refresh_token({"sub": "u1", "role": "ALUNO"})
    payload = verify_token(token, token_type="refresh")
    assert payload["type"] == "refresh"


@pytest.mark.unit
def test_verify_token_access_com_token_refresh_lanca_401():
    """Usar refresh token onde se espera access deve lançar HTTP 401."""
    refresh = create_refresh_token({"sub": "u1", "role": "ALUNO"})
    with pytest.raises(HTTPException) as exc:
        verify_token(refresh, token_type="access")
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_verify_token_adulterado_lanca_401():
    """Token adulterado (assinatura inválida) deve lançar HTTP 401."""
    token = create_access_token({"sub": "u1", "role": "ALUNO"})
    tampered = token[:-5] + "AAAAA"
    with pytest.raises(HTTPException) as exc:
        verify_token(tampered)
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_verify_token_expirado_lanca_401():
    """Token com expiração no passado deve lançar HTTP 401."""
    token = create_access_token(
        {"sub": "u1", "role": "ALUNO"},
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_verify_token_completamente_invalido():
    """String aleatória não é um JWT válido — deve lançar HTTP 401."""
    with pytest.raises(HTTPException) as exc:
        verify_token("nao.e.um.jwt.valido")
    assert exc.value.status_code == 401


@pytest.mark.unit
def test_access_e_refresh_tokens_sao_diferentes():
    """Access token e refresh token gerados com os mesmos dados não devem ser iguais."""
    data = {"sub": "u1", "role": "ALUNO"}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    assert access != refresh


# ── get_current_user ──────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_sucesso():
    """get_current_user retorna usuário quando token é válido e user existe."""
    from app.security.jwt import get_current_user
    from app.models.user import User, UserProgress

    user = User(
        _id="u1", name="João", email="joao@etec.sp.gov.br",
        hashed_password="$2b$12$aaa",
        role=UserRole.ALUNO, class_name="3A", is_active=True,
        progress=UserProgress(),
    )
    token = create_access_token({"sub": "u1", "role": "ALUNO"})

    # get_database e UserRepository são importados localmente → patch na fonte
    with patch("app.core.database.get_database", return_value=MagicMock()):
        with patch("app.repositories.user_repository.UserRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.find_by_id = AsyncMock(return_value=user)
            result = await get_current_user(token=token)

    assert result.id == "u1"
    assert result.is_active is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_sem_sub_lanca_401():
    """Token sem 'sub' deve lançar HTTP 401."""
    from app.security.jwt import get_current_user
    from jose import jwt as jose_jwt
    from app.core.config import settings

    token_no_sub = jose_jwt.encode(
        {"role": "ALUNO", "type": "access"},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token_no_sub)
    assert exc.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_usuario_nao_encontrado_lanca_401():
    """Usuário não existente no banco deve lançar HTTP 401."""
    from app.security.jwt import get_current_user

    token = create_access_token({"sub": "inexistente", "role": "ALUNO"})

    with patch("app.core.database.get_database", return_value=MagicMock()):
        with patch("app.repositories.user_repository.UserRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.find_by_id = AsyncMock(return_value=None)
            with pytest.raises(HTTPException) as exc:
                await get_current_user(token=token)

    assert exc.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_usuario_inativo_lanca_403():
    """Usuário inativo deve lançar HTTP 403."""
    from app.security.jwt import get_current_user
    from app.models.user import User, UserProgress

    inactive = User(
        _id="u_inativo", name="Inativo", email="i@etec.sp.gov.br",
        hashed_password="$2b$12$aaa",
        role=UserRole.ALUNO, class_name="3A", is_active=False,
        progress=UserProgress(),
    )
    token = create_access_token({"sub": "u_inativo", "role": "ALUNO"})

    with patch("app.core.database.get_database", return_value=MagicMock()):
        with patch("app.repositories.user_repository.UserRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.find_by_id = AsyncMock(return_value=inactive)
            with pytest.raises(HTTPException) as exc:
                await get_current_user(token=token)

    assert exc.value.status_code == 403


# ── get_current_active_user ───────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_active_user_retorna_usuario():
    """get_current_active_user é passthrough — retorna o user recebido."""
    from app.security.jwt import get_current_active_user
    from app.models.user import User, UserProgress

    user = User(
        _id="u2", name="Maria", email="maria@etec.sp.gov.br",
        hashed_password="$2b$12$bbb",
        role=UserRole.PROFESSOR, class_name=None, is_active=True,
        progress=UserProgress(),
    )
    result = await get_current_active_user(user=user)
    assert result.id == "u2"


# ── require_role ──────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_role_papel_correto_nao_lanca():
    """require_role não deve lançar quando usuário tem o papel exigido."""
    from app.security.jwt import require_role
    from app.models.user import User, UserProgress

    professor = User(
        _id="p1", name="Prof", email="p@etec.sp.gov.br",
        hashed_password="$2b$12$ccc",
        role=UserRole.PROFESSOR, class_name=None, is_active=True,
        progress=UserProgress(),
    )
    checker = require_role(UserRole.PROFESSOR)
    result = await checker(user=professor)
    assert result.role == UserRole.PROFESSOR


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_role_papel_incorreto_lanca_403():
    """require_role deve lançar HTTP 403 quando usuário não tem o papel exigido."""
    from app.security.jwt import require_role
    from app.models.user import User, UserProgress

    aluno = User(
        _id="a1", name="Aluno", email="a@etec.sp.gov.br",
        hashed_password="$2b$12$ddd",
        role=UserRole.ALUNO, class_name="3A", is_active=True,
        progress=UserProgress(),
    )
    checker = require_role(UserRole.PROFESSOR, UserRole.ADMINISTRADOR)
    with pytest.raises(HTTPException) as exc:
        await checker(user=aluno)
    assert exc.value.status_code == 403


@pytest.mark.unit
@pytest.mark.asyncio
async def test_require_role_multiplos_papeis_aceita_qualquer():
    """require_role com múltiplos papéis aceita qualquer um deles."""
    from app.security.jwt import require_role
    from app.models.user import User, UserProgress

    admin = User(
        _id="adm1", name="Admin", email="adm@etec.sp.gov.br",
        hashed_password="$2b$12$eee",
        role=UserRole.ADMINISTRADOR, class_name=None, is_active=True,
        progress=UserProgress(),
    )
    checker = require_role(UserRole.PROFESSOR, UserRole.ADMINISTRADOR)
    result = await checker(user=admin)
    assert result.role == UserRole.ADMINISTRADOR
