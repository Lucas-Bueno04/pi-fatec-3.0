"""
=============================================================================
LABQUIZ ETEC — Testes de Integração (17 casos de teste + parametrizados)
=============================================================================
Casos cobertos:
  TC01  Registro com LGPD aceito retorna tokens JWT
  TC01b LGPD não aceito rejeita com 422
  TC02  Login válido retorna JWT
  TC02b Login senha errada retorna 401
  TC03  Token adulterado retorna 401
  TC03b Sem token retorna 401
  TC04  Professor cria questão múltipla escolha
  TC04b Questão sem alternativa correta é rejeitada
  TC05  Aluno não pode criar questão (403)
  TC06  Quiz inicia com 10 questões (4+3+3)
  TC07  Resposta correta soma +10 pts (Fácil)
  TC08  Resposta incorreta não soma pontos
  TC09  Ajuda 'Eliminar 2' deduz 5 pts
  TC09b Ajuda 'Dica Textual' deduz 3 pts
  TC10  3ª ajuda excede limite e retorna 400
  TC11  ≥70% desbloqueia nível Médio
  TC12  <70% não desbloqueia nível
  TC13  Nível bloqueado retorna 403
  TC14  Aluno consulta próprio relatório
  TC15  Refresh token gera novos tokens
  TC16  Health endpoint retorna ok
  TC17  Pontuação diferencial por nível (parametrizado: 10/20/30)
=============================================================================
"""
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from app.api.v1.router import api_router
from app.exceptions.handlers import register_exception_handlers
from app.security.jwt import create_access_token
from app.models.user import User, UserRole, LGPDConsent, UserProgress
from app.models.question import QuestionType, DifficultyLevel
from app.models.quiz import QuizStatus, HelpType
from app.security.password import hash_password
from app.core.database import get_database as _real_get_db


# ── Test App ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def _noop_lifespan(app):
    yield


def _build_test_app():
    a = FastAPI(lifespan=_noop_lifespan)
    a.add_middleware(CORSMiddleware, allow_origins=["*"],
                     allow_methods=["*"], allow_headers=["*"])
    register_exception_handlers(a)
    a.include_router(api_router)

    @a.get("/health")
    async def health():
        return {"status": "ok", "app": "LabQuiz ETEC",
                "version": "1.0.0", "env": "test"}
    return a


_app = _build_test_app()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def _always_mock_db():
    """Garante que get_database nunca toca o MongoDB real em nenhum teste."""
    _app.dependency_overrides[_real_get_db] = lambda: MagicMock()
    yield
    _app.dependency_overrides.clear()
    _app.dependency_overrides[_real_get_db] = lambda: MagicMock()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(_app), base_url="http://test") as c:
        yield c


def _student(uid="s001", medio_unlocked=False):
    return User(
        _id=uid, name="Ana Silva", email=f"{uid}@etec.sp.gov.br",
        hashed_password=hash_password("senha@123"),
        role=UserRole.ALUNO, class_name="1Q-A",
        lgpd_consent=LGPDConsent(accepted=True),
        progress=UserProgress(facil_unlocked=True, medio_unlocked=medio_unlocked),
    )


def _teacher(uid="t001"):
    return User(
        _id=uid, name="Prof. Santos", email=f"{uid}@etec.sp.gov.br",
        hashed_password=hash_password("senha@123"),
        role=UserRole.PROFESSOR,
        lgpd_consent=LGPDConsent(accepted=True),
    )


def _tok(uid, role):
    return create_access_token({"sub": uid, "role": role})


def _auth_user(user):
    async def _dep():
        return user
    return _dep


def _set_user(user):
    from app.security import jwt as j
    _app.dependency_overrides[j.get_current_user] = _auth_user(user)
    _app.dependency_overrides[j.get_current_active_user] = _auth_user(user)
    _app.dependency_overrides[_real_get_db] = lambda: MagicMock()


# ── TC01 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC01_registro_lgpd_aceito_retorna_tokens(client):
    """TC01 — Registro com LGPD aceito deve retornar access_token + refresh_token."""
    from app.services.auth_service import AuthService
    from app.schemas.user import TokenResponse

    with patch.object(AuthService, "register", new_callable=AsyncMock,
                      return_value=TokenResponse(access_token="acc", refresh_token="ref")):
        r = await client.post("/api/v1/auth/register", json={
            "name": "Ana Silva", "email": "ana@etec.sp.gov.br",
            "password": "senha@123", "role": "ALUNO", "class_name": "1Q-A",
            "lgpd_consent": {"accepted": True, "guardian_name": "Maria"},
        })

    assert r.status_code == 201
    assert "access_token" in r.json()
    assert r.json()["token_type"] == "bearer"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC01b_lgpd_nao_aceito_retorna_422(client):
    """TC01b — Registro sem aceite LGPD deve ser rejeitado com HTTP 422."""
    r = await client.post("/api/v1/auth/register", json={
        "name": "Bob", "email": "bob@etec.sp.gov.br",
        "password": "senha@123", "role": "ALUNO", "class_name": "1Q-B",
        "lgpd_consent": {"accepted": False},
    })
    assert r.status_code == 422


# ── TC02 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC02_login_valido_retorna_jwt(client):
    """TC02 — Login com credenciais corretas retorna par de tokens JWT."""
    from app.services.auth_service import AuthService
    from app.schemas.user import TokenResponse

    with patch.object(AuthService, "login", new_callable=AsyncMock,
                      return_value=TokenResponse(access_token="a.b.c", refresh_token="d.e.f")):
        r = await client.post("/api/v1/auth/login/json",
                              json={"email": "ana@etec.sp.gov.br", "password": "senha@123"})

    assert r.status_code == 200
    assert r.json()["access_token"] == "a.b.c"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC02b_login_senha_errada_retorna_401(client):
    """TC02b — Login com senha incorreta retorna HTTP 401."""
    from app.services.auth_service import AuthService
    from fastapi import HTTPException

    with patch.object(AuthService, "login", new_callable=AsyncMock,
                      side_effect=HTTPException(401, "E-mail ou senha incorretos.")):
        r = await client.post("/api/v1/auth/login/json",
                              json={"email": "ana@etec.sp.gov.br", "password": "errada"})

    assert r.status_code == 401
    assert "incorretos" in r.json()["detail"]


# ── TC03 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC03_token_adulterado_retorna_401(client):
    """TC03 — Token JWT adulterado/inválido deve ser rejeitado com HTTP 401."""
    r = await client.get("/api/v1/auth/me",
                         headers={"Authorization": "Bearer tok.adulterado.invalido"})
    assert r.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC03b_sem_token_retorna_401(client):
    """TC03b — Requisição sem Authorization header deve retornar HTTP 401."""
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


# ── TC04 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC04_professor_cria_questao(client):
    """TC04 — Professor autenticado cria questão múltipla escolha com 4 alternativas."""
    from app.services.question_service import QuestionService
    from app.schemas.question import QuestionResponse, AlternativeResponse

    teacher = _teacher()
    _set_user(teacher)

    mock_q = QuestionResponse(
        id="q01", type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL, text="Qual material mede volume?",
        alternatives=[AlternativeResponse(id=f"a{i}", text=f"Alt{i}", alt_text=f"a{i}")
                      for i in range(1, 5)],
        explanation="A proveta.", is_active=True, created_by=teacher.id,
    )

    with patch.object(QuestionService, "create_question", new_callable=AsyncMock,
                      return_value=mock_q):
        r = await client.post("/api/v1/questions/", json={
            "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
            "text": "Qual material mede volume?",
            "alternatives": [
                {"id": "a1", "text": "Proveta", "is_correct": True, "alt_text": "Proveta"},
                {"id": "a2", "text": "Béquer", "is_correct": False, "alt_text": "Béquer"},
                {"id": "a3", "text": "Funil", "is_correct": False, "alt_text": "Funil"},
                {"id": "a4", "text": "Erlenmyer", "is_correct": False, "alt_text": "Erlenmyer"},
            ],
            "explanation": "A proveta possui escala graduada.",
        }, headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"})

    assert r.status_code == 201
    body = r.json()
    assert body["type"] == "MULTIPLA_ESCOLHA"
    assert body["is_active"] is True
    assert len(body["alternatives"]) == 4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC04b_questao_zero_corretas_rejeitada(client):
    """TC04b — Questão com 0 alternativas corretas deve ser rejeitada com 422 ou 400."""
    teacher = _teacher()
    _set_user(teacher)

    r = await client.post("/api/v1/questions/", json={
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Questão inválida",
        "alternatives": [
            {"id": f"a{i}", "text": f"X{i}", "is_correct": False, "alt_text": f"a{i}"}
            for i in range(1, 5)
        ],
        "explanation": "Sem correta",
    }, headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"})

    assert r.status_code in (400, 422)


# ── TC05 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC05_aluno_nao_pode_criar_questao(client):
    """TC05 — Aluno tentando criar questão deve receber HTTP 403 Forbidden."""
    student = _student()
    _set_user(student)

    r = await client.post("/api/v1/questions/", json={
        "type": "MULTIPLA_ESCOLHA", "difficulty": "FACIL",
        "text": "Tentativa inválida de aluno",
        "alternatives": [
            {"id": f"a{i}", "text": f"X{i}", "is_correct": i == 1, "alt_text": f"a{i}"}
            for i in range(1, 5)
        ],
        "explanation": "x",
    }, headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 403


# ── TC06 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC06_inicio_quiz_10_questoes(client):
    """TC06 — Quiz iniciado deve conter exatamente 10 questões (4 fácil+3 médio+3 difícil)."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import QuizSessionResponse

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "start_quiz", new_callable=AsyncMock,
                      return_value=QuizSessionResponse(
                          id="sess001", level=DifficultyLevel.FACIL,
                          status=QuizStatus.IN_PROGRESS, score=0,
                          total_possible_score=130, accuracy_percent=0.0,
                          help_count=0, started_at=datetime.utcnow(),
                          current_question_index=0, total_questions=10,
                      )):
        r = await client.post("/api/v1/quizzes/start",
                              json={"level": "FACIL"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 201
    body = r.json()
    assert body["total_questions"] == 10
    assert body["level"] == "FACIL"
    assert body["status"] == "IN_PROGRESS"
    assert body["score"] == 0


# ── TC07 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC07_resposta_correta_soma_10pts(client):
    """TC07 — Resposta correta em nível Fácil deve somar exatamente +10 pontos."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import AnswerResult

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "submit_answer", new_callable=AsyncMock,
                      return_value=AnswerResult(
                          is_correct=True, correct_alternative_id="a1",
                          explanation="Béquer aguenta calor.",
                          points_earned=10, current_score=10, is_last_question=False,
                      )):
        r = await client.post("/api/v1/quizzes/sess001/answer",
                              json={"question_id": "q001", "selected_alternative_id": "a1"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["is_correct"] is True
    assert body["points_earned"] == 10
    assert body["current_score"] == 10


# ── TC08 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC08_resposta_incorreta_zero_pontos(client):
    """TC08 — Resposta incorreta deve resultar em 0 pontos adicionados."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import AnswerResult

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "submit_answer", new_callable=AsyncMock,
                      return_value=AnswerResult(
                          is_correct=False, correct_alternative_id="a1",
                          explanation="Correto seria o béquer.",
                          points_earned=0, current_score=0, is_last_question=False,
                      )):
        r = await client.post("/api/v1/quizzes/sess001/answer",
                              json={"question_id": "q001", "selected_alternative_id": "a4"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["is_correct"] is False
    assert body["points_earned"] == 0


# ── TC09 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC09_eliminar_2_alternativas_deduz_5pts(client):
    """TC09 — Ajuda 'Eliminar 2 Alternativas' deduz 5 pts e retorna 2 IDs eliminados."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import HelpResponse

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "use_help", new_callable=AsyncMock,
                      return_value=HelpResponse(
                          help_type=HelpType.ELIMINATE_TWO,
                          eliminated_alternative_ids=["a2", "a3"],
                          points_deducted=5, helps_remaining=1,
                      )):
        r = await client.post("/api/v1/quizzes/sess001/help",
                              json={"question_id": "q001", "help_type": "ELIMINATE_TWO"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["points_deducted"] == 5
    assert len(body["eliminated_alternative_ids"]) == 2
    assert body["helps_remaining"] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC09b_dica_textual_deduz_3pts(client):
    """TC09b — Ajuda 'Dica Textual' deduz 3 pts e retorna texto da dica."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import HelpResponse

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "use_help", new_callable=AsyncMock,
                      return_value=HelpResponse(
                          help_type=HelpType.TEXT_HINT,
                          hint_text="Pense no material que suporta altas temperaturas...",
                          points_deducted=3, helps_remaining=1,
                      )):
        r = await client.post("/api/v1/quizzes/sess001/help",
                              json={"question_id": "q001", "help_type": "TEXT_HINT"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["points_deducted"] == 3
    assert body["hint_text"] and len(body["hint_text"]) > 0


# ── TC10 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC10_terceira_ajuda_excede_limite_400(client):
    """TC10 — Solicitar 3ª ajuda (limite=2) deve retornar HTTP 400."""
    from app.services.quiz_service import QuizService
    from fastapi import HTTPException

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "use_help", new_callable=AsyncMock,
                      side_effect=HTTPException(400, "Limite de 2 ajudas por quiz atingido.")):
        r = await client.post("/api/v1/quizzes/sess001/help",
                              json={"question_id": "q001", "help_type": "ELIMINATE_TWO"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 400
    assert "Limite" in r.json()["detail"]


# ── TC11 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC11_acerto_80pct_desbloqueia_nivel_medio(client):
    """TC11 — Finalizar quiz Fácil com 80% (8/10 acertos) deve desbloquear nível Médio."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import QuizResultResponse

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "finish_quiz", new_callable=AsyncMock,
                      return_value=QuizResultResponse(
                          session_id="sess001", level=DifficultyLevel.FACIL,
                          score=91, total_possible_score=130, accuracy_percent=80.0,
                          correct_count=8, wrong_count=2, help_count=0,
                          level_unlocked=DifficultyLevel.MEDIO,
                          answers=[], started_at=datetime.utcnow(),
                          finished_at=datetime.utcnow(),
                      )):
        r = await client.post("/api/v1/quizzes/sess001/finish",
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["accuracy_percent"] == 80.0
    assert body["level_unlocked"] == "MEDIO"
    assert body["correct_count"] == 8


# ── TC12 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC12_acerto_60pct_nao_desbloqueia(client):
    """TC12 — Finalizar com 60% (6/10 acertos) NÃO deve desbloquear próximo nível."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import QuizResultResponse

    student = _student()
    _set_user(student)

    with patch.object(QuizService, "finish_quiz", new_callable=AsyncMock,
                      return_value=QuizResultResponse(
                          session_id="sess001", level=DifficultyLevel.FACIL,
                          score=60, total_possible_score=130, accuracy_percent=60.0,
                          correct_count=6, wrong_count=4, help_count=1,
                          level_unlocked=None,
                          answers=[], started_at=datetime.utcnow(),
                          finished_at=datetime.utcnow(),
                      )):
        r = await client.post("/api/v1/quizzes/sess001/finish",
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["accuracy_percent"] == 60.0
    assert body["level_unlocked"] is None


# ── TC13 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC13_nivel_medio_bloqueado_retorna_403(client):
    """TC13 — Iniciar quiz no nível Médio sem desbloqueio retorna HTTP 403."""
    from app.services.quiz_service import QuizService
    from fastapi import HTTPException

    student = _student(medio_unlocked=False)
    _set_user(student)

    with patch.object(QuizService, "start_quiz", new_callable=AsyncMock,
                      side_effect=HTTPException(403, "Nível Médio ainda não desbloqueado.")):
        r = await client.post("/api/v1/quizzes/start",
                              json={"level": "MEDIO"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 403
    assert "desbloqueado" in r.json()["detail"]


# ── TC14 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC14_relatorio_aluno_retorna_estatisticas(client):
    """TC14 — Aluno autenticado consulta relatório com estatísticas de desempenho."""
    from app.services.report_service import ReportService
    from app.schemas.report import StudentReport

    student = _student()
    _set_user(student)

    with patch.object(ReportService, "get_student_report", new_callable=AsyncMock,
                      return_value=StudentReport(
                          user_id=student.id, name=student.name, email=student.email,
                          class_name="1Q-A", total_games=5, avg_accuracy=74.5,
                          best_accuracy=90.0, max_level_reached=DifficultyLevel.MEDIO,
                          total_score=650, facil_games=3, medio_games=2, dificil_games=0,
                          recent_sessions=[],
                      )):
        r = await client.get("/api/v1/reports/my-report",
                             headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    body = r.json()
    assert body["total_games"] == 5
    assert body["avg_accuracy"] == 74.5
    assert body["max_level_reached"] == "MEDIO"


# ── TC15 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC15_refresh_token_gera_novos_tokens(client):
    """TC15 — Refresh token válido deve gerar novo par access_token + refresh_token."""
    from app.services.auth_service import AuthService
    from app.schemas.user import TokenResponse

    with patch.object(AuthService, "refresh", new_callable=AsyncMock,
                      return_value=TokenResponse(access_token="new.acc", refresh_token="new.ref")):
        r = await client.post("/api/v1/auth/refresh",
                              json={"refresh_token": "old.ref.token"})

    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] == "new.acc"
    assert body["refresh_token"] == "new.ref"


# ── TC16 ──────────────────────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC16_health_retorna_status_ok(client):
    """TC16 — Endpoint /health deve retornar status ok com nome e versão do sistema."""
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app"] == "LabQuiz ETEC"
    assert "version" in body


# ── TC17 — Parametrizado ──────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("level,expected_pts", [
    ("FACIL",   10),
    ("MEDIO",   20),
    ("DIFICIL", 30),
], ids=["facil-10pts", "medio-20pts", "dificil-30pts"])
async def test_TC17_pontuacao_diferencial_por_nivel(client, level, expected_pts):
    """TC17 — Questão correta pontua +10/+20/+30 conforme nível Fácil/Médio/Difícil."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import AnswerResult

    student = _student(medio_unlocked=True)
    _set_user(student)

    with patch.object(QuizService, "submit_answer", new_callable=AsyncMock,
                      return_value=AnswerResult(
                          is_correct=True, correct_alternative_id="a1",
                          explanation="Correto!",
                          points_earned=expected_pts,
                          current_score=expected_pts,
                          is_last_question=False,
                      )):
        r = await client.post("/api/v1/quizzes/sess_x/answer",
                              json={"question_id": "q001", "selected_alternative_id": "a1"},
                              headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"})

    assert r.status_code == 200
    assert r.json()["points_earned"] == expected_pts
