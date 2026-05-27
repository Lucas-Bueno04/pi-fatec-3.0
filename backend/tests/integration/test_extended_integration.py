"""
=============================================================================
LABQUIZ ETEC — Testes de Integração Estendidos (TC18–TC30)
=============================================================================
TC18  Listar questões com filtro de dificuldade
TC19  Atualizar questão (professor)
TC20  Deletar questão (soft delete)
TC21  Resposta de associação correta
TC22  Resposta duplicada na mesma sessão é rejeitada (400)
TC23  Listagem de usuários só para administrador
TC24  Relatório da turma (professor)
TC25  Dashboard do professor
TC26  Atualizar perfil do usuário autenticado
TC27  Histórico de quizzes do aluno
TC28  Sessão não encontrada retorna 404
TC29  Aluno não pode acessar relatório de turma (403)
TC30  Endpoint /api/v1 raiz retorna 404 (rota inexistente)
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
from app.models.question import QuestionType, DifficultyLevel, Question, Alternative
from app.models.quiz import QuizSession, QuizStatus, QuizAnswer
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
        return {"status": "ok", "app": "LabQuiz ETEC", "version": "1.0.0", "env": "test"}
    return a


_app = _build_test_app()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def _always_mock_db():
    _app.dependency_overrides[_real_get_db] = lambda: MagicMock()
    yield
    _app.dependency_overrides.clear()
    _app.dependency_overrides[_real_get_db] = lambda: MagicMock()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(_app), base_url="http://test") as c:
        yield c


def _user(uid, role=UserRole.ALUNO, class_name="1Q-A", medio_unlocked=False):
    return User(
        _id=uid, name=f"User {uid}", email=f"{uid}@etec.sp",
        hashed_password=hash_password("senha@123"),
        role=role, class_name=class_name,
        lgpd_consent=LGPDConsent(accepted=True),
        progress=UserProgress(facil_unlocked=True, medio_unlocked=medio_unlocked),
    )


def _tok(uid, role):
    return create_access_token({"sub": uid, "role": role})


def _set_user(user):
    from app.security import jwt as j
    _app.dependency_overrides[j.get_current_user] = lambda: user
    _app.dependency_overrides[j.get_current_active_user] = lambda: user
    _app.dependency_overrides[_real_get_db] = lambda: MagicMock()


def _mc_question_response(qid="q01"):
    from app.schemas.question import QuestionResponse, AlternativeResponse
    return QuestionResponse(
        id=qid, type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL, text="Qual vidraria mede volume?",
        alternatives=[AlternativeResponse(id=f"a{i}", text=f"Alt{i}") for i in range(1, 5)],
        explanation="A proveta.", is_active=True, created_by="t001",
    )


# ── TC18 — Listar questões com filtro ─────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC18_listar_questoes_com_filtro_dificuldade(client):
    """TC18 — GET /questions?difficulty=MEDIO deve retornar apenas questões médias."""
    from app.services.question_service import QuestionService
    from app.schemas.question import QuestionResponse, AlternativeResponse

    student = _user("s001")
    _set_user(student)

    qs = [_mc_question_response(f"q{i}") for i in range(3)]
    for q in qs:
        q.difficulty = DifficultyLevel.MEDIO

    with patch.object(QuestionService, "list_questions", new_callable=AsyncMock, return_value=qs):
        r = await client.get(
            "/api/v1/questions/?difficulty=MEDIO",
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == 3


# ── TC19 — Atualizar questão ──────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC19_professor_atualiza_questao(client):
    """TC19 — Professor pode atualizar texto de questão existente."""
    from app.services.question_service import QuestionService

    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    _set_user(teacher)

    updated_q = _mc_question_response("q01")
    updated_q.text = "Texto atualizado"

    with patch.object(QuestionService, "update_question", new_callable=AsyncMock,
                      return_value=updated_q):
        r = await client.put(
            "/api/v1/questions/q01",
            json={"text": "Texto atualizado"},
            headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"},
        )

    assert r.status_code == 200
    assert r.json()["text"] == "Texto atualizado"


# ── TC20 — Deletar questão ────────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC20_professor_deleta_questao(client):
    """TC20 — Soft delete de questão retorna HTTP 204."""
    from app.services.question_service import QuestionService

    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    _set_user(teacher)

    with patch.object(QuestionService, "delete_question", new_callable=AsyncMock, return_value=None):
        r = await client.delete(
            "/api/v1/questions/q01",
            headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"},
        )

    assert r.status_code == 204


# ── TC21 — Resposta de associação correta ─────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC21_resposta_associacao_correta(client):
    """TC21 — Resposta de associação com mapeamento correto retorna is_correct=True."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import AnswerResult

    student = _user("s001")
    _set_user(student)

    with patch.object(QuizService, "submit_answer", new_callable=AsyncMock,
                      return_value=AnswerResult(
                          is_correct=True, explanation="Correto!",
                          points_earned=20, current_score=20, is_last_question=False,
                      )):
        r = await client.post(
            "/api/v1/quizzes/sess001/answer",
            json={"question_id": "qa1", "association_answers": {"m1": "t1", "m2": "t2"}},
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["is_correct"] is True
    assert body["points_earned"] == 20


# ── TC22 — Resposta duplicada ─────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC22_resposta_duplicada_retorna_400(client):
    """TC22 — Submeter resposta para questão já respondida retorna HTTP 400."""
    from app.services.quiz_service import QuizService
    from fastapi import HTTPException

    student = _user("s001")
    _set_user(student)

    with patch.object(QuizService, "submit_answer", new_callable=AsyncMock,
                      side_effect=HTTPException(400, "Questão já respondida.")):
        r = await client.post(
            "/api/v1/quizzes/sess001/answer",
            json={"question_id": "q001", "selected_alternative_id": "a1"},
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 400
    assert "respondida" in r.json()["detail"]


# ── TC23 — Listagem de usuários (admin) ───────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC23_listar_usuarios_apenas_admin(client):
    """TC23 — Apenas ADMINISTRADOR pode listar todos os usuários."""
    from app.repositories.user_repository import UserRepository

    admin = _user("a001", role=UserRole.ADMINISTRADOR, class_name=None)
    _set_user(admin)

    users = [_user(f"s{i}") for i in range(5)]

    with patch.object(UserRepository, "find_many", new_callable=AsyncMock, return_value=users):
        r = await client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {_tok(admin.id, 'ADMINISTRADOR')}"},
        )

    assert r.status_code == 200
    assert len(r.json()) == 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC23b_aluno_nao_pode_listar_usuarios(client):
    """TC23b — Aluno tentando listar usuários recebe HTTP 403."""
    student = _user("s001")
    _set_user(student)

    r = await client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
    )

    assert r.status_code == 403


# ── TC24 — Relatório da turma ─────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC24_relatorio_turma_professor(client):
    """TC24 — Professor obtém relatório de uma turma."""
    from app.services.report_service import ReportService
    from app.schemas.report import ClassReport

    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    _set_user(teacher)

    with patch.object(ReportService, "get_class_report", new_callable=AsyncMock,
                      return_value=ClassReport(
                          class_name="1Q-A", total_students=10,
                          avg_accuracy=72.5, students=[],
                      )):
        r = await client.get(
            "/api/v1/reports/class/1Q-A",
            headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["class_name"] == "1Q-A"
    assert body["total_students"] == 10
    assert body["avg_accuracy"] == 72.5


# ── TC25 — Dashboard do professor ─────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC25_dashboard_professor(client):
    """TC25 — Professor acessa dashboard pedagógico com dados reais."""
    from app.services.report_service import ReportService
    from app.schemas.report import TeacherDashboard

    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    _set_user(teacher)

    with patch.object(ReportService, "get_teacher_dashboard", new_callable=AsyncMock,
                      return_value=TeacherDashboard(
                          total_students=25, total_games_today=8,
                          avg_accuracy_this_week=68.3,
                          top_students=[], struggling_students=[],
                      )):
        r = await client.get(
            "/api/v1/reports/dashboard",
            headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["total_students"] == 25
    assert body["total_games_today"] == 8


# ── TC26 — Atualizar perfil ───────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC26_aluno_atualiza_proprio_perfil(client):
    """TC26 — Aluno pode atualizar seu próprio nome."""
    from app.repositories.user_repository import UserRepository

    student = _user("s001")
    _set_user(student)

    updated = _user("s001")
    updated.name = "Ana Carolina"

    with patch.object(UserRepository, "update_user", new_callable=AsyncMock,
                      return_value=updated):
        r = await client.put(
            "/api/v1/auth/me",
            json={"name": "Ana Carolina"},
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 200
    assert r.json()["name"] == "Ana Carolina"


# ── TC27 — Histórico de quizzes ───────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC27_historico_quizzes_aluno(client):
    """TC27 — Aluno consulta seu histórico de quizzes."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import QuizSessionResponse

    student = _user("s001")
    _set_user(student)

    history = [
        QuizSessionResponse(
            id=f"sess{i}", level=DifficultyLevel.FACIL,
            status=QuizStatus.COMPLETED, score=i * 30,
            total_possible_score=130, accuracy_percent=float(i * 20),
            help_count=0, started_at=datetime.utcnow(),
            current_question_index=10, total_questions=10,
        )
        for i in range(4)
    ]

    with patch.object(QuizService, "get_history", new_callable=AsyncMock, return_value=history):
        r = await client.get(
            "/api/v1/quizzes/history",
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 200
    assert len(r.json()) == 4


# ── TC28 — Sessão não encontrada ──────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC28_sessao_nao_encontrada_retorna_404(client):
    """TC28 — Busca de sessão inexistente retorna HTTP 404."""
    from app.repositories.quiz_repository import QuizRepository

    student = _user("s001")
    _set_user(student)

    with patch.object(QuizRepository, "find_by_id", new_callable=AsyncMock, return_value=None):
        r = await client.get(
            "/api/v1/quizzes/sessao_ghost",
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 404


# ── TC29 — Aluno sem acesso a relatório de turma ──────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC29_aluno_nao_acessa_relatorio_turma(client):
    """TC29 — Aluno tentando acessar relatório de turma recebe HTTP 403."""
    student = _user("s001")
    _set_user(student)

    r = await client.get(
        "/api/v1/reports/class/1Q-A",
        headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
    )

    assert r.status_code == 403


# ── TC30 — Rota inexistente ───────────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC30_rota_inexistente_retorna_404(client):
    """TC30 — Acesso a rota que não existe retorna HTTP 404."""
    r = await client.get("/api/v1/rota_que_nao_existe")
    assert r.status_code == 404


# ── TC31 — GET /auth/me retorna dados completos ───────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC31_get_me_retorna_dados_usuario(client):
    """TC31 — /auth/me retorna dados completos do usuário autenticado."""
    student = _user("s001")
    _set_user(student)

    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
    )

    assert r.status_code == 200
    body = r.json()
    assert body["email"] == f"s001@etec.sp"
    assert body["role"] == "ALUNO"
    assert "progress" in body


# ── TC32 — Questão não encontrada ─────────────────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC32_questao_nao_encontrada_retorna_404(client):
    """TC32 — GET /questions/{id} com ID inexistente retorna HTTP 404."""
    from app.services.question_service import QuestionService
    from fastapi import HTTPException

    student = _user("s001")
    _set_user(student)

    with patch.object(QuestionService, "get_question", new_callable=AsyncMock,
                      side_effect=HTTPException(404, "Questão não encontrada.")):
        r = await client.get(
            "/api/v1/questions/nao_existe",
            headers={"Authorization": f"Bearer {_tok(student.id, 'ALUNO')}"},
        )

    assert r.status_code == 404


# ── TC33 — Relatório individual pelo professor ────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC33_professor_consulta_relatorio_aluno(client):
    """TC33 — Professor pode consultar relatório de aluno específico."""
    from app.services.report_service import ReportService
    from app.schemas.report import StudentReport

    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    _set_user(teacher)

    with patch.object(ReportService, "get_student_report", new_callable=AsyncMock,
                      return_value=StudentReport(
                          user_id="s001", name="Ana", email="s001@etec.sp",
                          class_name="1Q-A", total_games=3, avg_accuracy=80.0,
                          best_accuracy=95.0, max_level_reached=DifficultyLevel.FACIL,
                          total_score=300, facil_games=3, medio_games=0, dificil_games=0,
                          recent_sessions=[],
                      )):
        r = await client.get(
            "/api/v1/reports/student/s001",
            headers={"Authorization": f"Bearer {_tok(teacher.id, 'PROFESSOR')}"},
        )

    assert r.status_code == 200
    body = r.json()
    assert body["total_games"] == 3
    assert body["best_accuracy"] == 95.0


# ── TC34 — Refresh token inválido retorna 401 ─────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_TC34_refresh_token_invalido_retorna_401(client):
    """TC34 — Refresh com token inválido retorna HTTP 401."""
    from app.services.auth_service import AuthService
    from fastapi import HTTPException

    with patch.object(AuthService, "refresh", new_callable=AsyncMock,
                      side_effect=HTTPException(401, "Token inválido.")):
        r = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token.invalido.aqui"},
        )

    assert r.status_code == 401


# ── TC35 — Parametrizado: pontuação por nível ─────────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("level,pts,role", [
    ("FACIL",   10, "ALUNO"),
    ("MEDIO",   20, "ALUNO"),
    ("DIFICIL", 30, "ALUNO"),
], ids=["facil-10pts", "medio-20pts", "dificil-30pts"])
async def test_TC35_pontuacao_diferencial_por_nivel(client, level, pts, role):
    """TC35 — Resposta correta pontua diferenciado por nível."""
    from app.services.quiz_service import QuizService
    from app.schemas.quiz import AnswerResult

    student = _user("s001", medio_unlocked=True)
    _set_user(student)

    with patch.object(QuizService, "submit_answer", new_callable=AsyncMock,
                      return_value=AnswerResult(
                          is_correct=True, explanation="Certo!",
                          points_earned=pts, current_score=pts,
                          is_last_question=False,
                      )):
        r = await client.post(
            "/api/v1/quizzes/sess_x/answer",
            json={"question_id": "q001", "selected_alternative_id": "a1"},
            headers={"Authorization": f"Bearer {_tok(student.id, role)}"},
        )

    assert r.status_code == 200
    assert r.json()["points_earned"] == pts
