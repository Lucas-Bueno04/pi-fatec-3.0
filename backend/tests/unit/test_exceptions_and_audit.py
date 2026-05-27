"""
=============================================================================
LABQUIZ ETEC — Testes unitários: Exceptions + AuditLog
=============================================================================
Cobre:
  - AppException e subclasses (QuizNotFoundException, LevelLockedError, …)
  - AuditLog.to_mongo / from_mongo
=============================================================================
"""
import pytest
from datetime import datetime


# ── Exception classes ─────────────────────────────────────────────────────────

@pytest.mark.unit
def test_app_exception_atributos():
    """AppException deve armazenar status_code e detail."""
    from app.exceptions.handlers import AppException
    exc = AppException(status_code=422, detail="Erro customizado")
    assert exc.status_code == 422
    assert exc.detail == "Erro customizado"


@pytest.mark.unit
def test_quiz_not_found_exception():
    """QuizNotFoundException deve ter status 404."""
    from app.exceptions.handlers import QuizNotFoundException
    exc = QuizNotFoundException()
    assert exc.status_code == 404
    assert "quiz" in exc.detail.lower() or "sessão" in exc.detail.lower()


@pytest.mark.unit
def test_level_locked_error():
    """LevelLockedError deve ter status 403 e incluir o nível na mensagem."""
    from app.exceptions.handlers import LevelLockedError
    exc = LevelLockedError("DIFICIL")
    assert exc.status_code == 403
    assert "DIFICIL" in exc.detail


@pytest.mark.unit
def test_help_limit_exceeded_error():
    """HelpLimitExceededError deve ter status 400."""
    from app.exceptions.handlers import HelpLimitExceededError
    exc = HelpLimitExceededError()
    assert exc.status_code == 400
    assert "ajuda" in exc.detail.lower() or "limit" in exc.detail.lower()


@pytest.mark.unit
def test_invalid_answer_error():
    """InvalidAnswerError deve ter status 400."""
    from app.exceptions.handlers import InvalidAnswerError
    exc = InvalidAnswerError()
    assert exc.status_code == 400


@pytest.mark.unit
def test_lgpd_consent_required_error():
    """LGPDConsentRequiredError deve ter status 400 e mencionar LGPD."""
    from app.exceptions.handlers import LGPDConsentRequiredError
    exc = LGPDConsentRequiredError()
    assert exc.status_code == 400
    assert "lgpd" in exc.detail.lower() or "consentimento" in exc.detail.lower()


@pytest.mark.unit
def test_app_exception_is_exception():
    """AppException deve ser subclasse de Exception."""
    from app.exceptions.handlers import AppException
    assert issubclass(AppException, Exception)


# ── AuditLog model ────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_audit_log_to_mongo():
    """to_mongo deve retornar dict sem campo 'id'."""
    from app.models.audit import AuditLog
    log = AuditLog(
        user_id="u1", action="LOGIN", resource="auth",
        resource_id="r1", ip_address="127.0.0.1",
    )
    data = log.to_mongo()
    assert isinstance(data, dict)
    assert "id" not in data
    assert data["action"] == "LOGIN"
    assert data["resource"] == "auth"
    assert data["user_id"] == "u1"


@pytest.mark.unit
def test_audit_log_from_mongo_converte_id():
    """from_mongo deve converter _id para string."""
    from app.models.audit import AuditLog
    from bson import ObjectId
    oid = ObjectId()
    raw = {
        "_id": oid,
        "user_id": "u2",
        "action": "QUIZ_START",
        "resource": "quiz",
        "timestamp": datetime.utcnow(),
        "details": {},
    }
    log = AuditLog.from_mongo(raw)
    assert log.id == str(oid)
    assert log.action == "QUIZ_START"


@pytest.mark.unit
def test_audit_log_from_mongo_sem_id():
    """from_mongo deve funcionar quando não há _id."""
    from app.models.audit import AuditLog
    raw = {
        "user_id": "u3",
        "action": "LOGOUT",
        "resource": "auth",
        "timestamp": datetime.utcnow(),
        "details": {},
    }
    log = AuditLog.from_mongo(raw)
    assert log.action == "LOGOUT"
    assert log.id is None


@pytest.mark.unit
def test_audit_log_defaults():
    """AuditLog deve ter timestamp preenchido por padrão."""
    from app.models.audit import AuditLog
    log = AuditLog(action="TEST", resource="tests")
    assert isinstance(log.timestamp, datetime)
    assert log.details == {}
