"""
=============================================================================
LABQUIZ ETEC — Testes unitários: ReportService
=============================================================================
Cobre:
  - get_student_report (com e sem sessões, filtros de data/nível)
  - get_class_report (turma vazia, turma com alunos)
  - get_teacher_dashboard (sem alunos, com alunos)
  - aluno não encontrado → HTTP 404
=============================================================================
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.report_service import ReportService
from app.models.user import User, UserRole, LGPDConsent, UserProgress
from app.models.quiz import QuizSession, QuizStatus, QuizAnswer
from app.models.question import DifficultyLevel
from app.security.password import hash_password


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user(uid, role=UserRole.ALUNO, class_name="1Q-A"):
    return User(
        _id=uid, name=f"User {uid}", email=f"{uid}@etec.sp",
        hashed_password=hash_password("senha123"),
        role=role, class_name=class_name,
        lgpd_consent=LGPDConsent(accepted=True),
        progress=UserProgress(),
    )


def _session(uid, level=DifficultyLevel.FACIL, accuracy=80.0, score=80,
             status=QuizStatus.COMPLETED, started_at=None):
    return QuizSession(
        _id=f"sess_{uid}_{level.value}",
        user_id=uid,
        level=level,
        question_ids=[f"q{i}" for i in range(10)],
        score=score,
        total_possible_score=130,
        accuracy_percent=accuracy,
        status=status,
        started_at=started_at or datetime.utcnow(),
    )


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ReportService(mock_db)


# ── get_student_report ────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_usuario_nao_encontrado(service):
    """HTTP 404 quando aluno não existe."""
    with patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            from app.schemas.report import ReportFilter
            await service.get_student_report("ghost", ReportFilter())
    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_sem_sessoes(service):
    """Relatório de aluno sem histórico retorna zeros."""
    from app.schemas.report import ReportFilter
    student = _user("s001")
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, return_value=[]),
    ):
        report = await service.get_student_report("s001", ReportFilter())
    assert report.total_games == 0
    assert report.avg_accuracy == 0.0
    assert report.best_accuracy == 0.0
    assert report.max_level_reached is None
    assert report.total_score == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_com_sessoes_completas(service):
    """Relatório calcula médias e pontuação total corretamente."""
    from app.schemas.report import ReportFilter
    student = _user("s001")
    sessions = [
        _session("s001", DifficultyLevel.FACIL, accuracy=80.0, score=80),
        _session("s001", DifficultyLevel.FACIL, accuracy=100.0, score=130),
        _session("s001", DifficultyLevel.MEDIO, accuracy=70.0, score=140),
    ]
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, return_value=sessions),
    ):
        report = await service.get_student_report("s001", ReportFilter())
    assert report.total_games == 3
    assert report.best_accuracy == 100.0
    assert report.total_score == 350
    assert report.avg_accuracy == round((80 + 100 + 70) / 3, 2)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_ignora_sessoes_abandonadas(service):
    """Sessões ABANDONED não devem contar no relatório."""
    from app.schemas.report import ReportFilter
    student = _user("s001")
    sessions = [
        _session("s001", accuracy=90.0, status=QuizStatus.COMPLETED),
        _session("s001", accuracy=50.0, status=QuizStatus.ABANDONED),
    ]
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, return_value=sessions),
    ):
        report = await service.get_student_report("s001", ReportFilter())
    assert report.total_games == 1  # apenas a completed
    assert report.avg_accuracy == 90.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_filtro_nivel(service):
    """Filtro por nível retorna apenas sessões do nível especificado."""
    from app.schemas.report import ReportFilter
    student = _user("s001")
    sessions = [
        _session("s001", DifficultyLevel.FACIL, accuracy=80.0),
        _session("s001", DifficultyLevel.MEDIO, accuracy=60.0),
        _session("s001", DifficultyLevel.DIFICIL, accuracy=90.0),
    ]
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, return_value=sessions),
    ):
        report = await service.get_student_report(
            "s001", ReportFilter(level=DifficultyLevel.FACIL)
        )
    assert report.total_games == 1
    assert report.facil_games == 1
    assert report.medio_games == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_max_level_reached(service):
    """max_level_reached deve ser o nível mais alto completado."""
    from app.schemas.report import ReportFilter
    student = _user("s001")
    sessions = [
        _session("s001", DifficultyLevel.FACIL, accuracy=80.0),
        _session("s001", DifficultyLevel.MEDIO, accuracy=75.0),
    ]
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, return_value=sessions),
    ):
        report = await service.get_student_report("s001", ReportFilter())
    assert report.max_level_reached == DifficultyLevel.MEDIO


@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_filtro_data(service):
    """Filtro date_from exclui sessões anteriores à data."""
    from app.schemas.report import ReportFilter
    student = _user("s001")
    cutoff = datetime.utcnow()
    old = _session("s001", accuracy=90.0,
                   started_at=cutoff - timedelta(days=10))
    new = _session("s001", accuracy=60.0,
                   started_at=cutoff + timedelta(seconds=1))
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, return_value=[old, new]),
    ):
        report = await service.get_student_report(
            "s001", ReportFilter(date_from=cutoff)
        )
    assert report.total_games == 1
    assert report.avg_accuracy == 60.0


# ── get_class_report ──────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_class_report_turma_vazia(service):
    """Relatório de turma sem alunos retorna zeros."""
    with (
        patch.object(service.user_repo, "list_by_class", new_callable=AsyncMock, return_value=[]),
    ):
        from app.schemas.report import ReportFilter
        report = await service.get_class_report("1Q-X", ReportFilter())
    assert report.total_students == 0
    assert report.avg_accuracy == 0.0
    assert report.students == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_class_report_com_alunos(service):
    """Relatório de turma agrega médias de todos os alunos."""
    from app.schemas.report import ReportFilter
    students = [_user(f"s{i}") for i in range(3)]
    sessions_per_student = [
        [_session(f"s{i}", accuracy=70.0 + i * 10)] for i in range(3)
    ]

    async def mock_find_user(uid, limit=100):
        idx = int(uid[1:])
        return sessions_per_student[idx]

    with (
        patch.object(service.user_repo, "list_by_class", new_callable=AsyncMock, return_value=students),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, side_effect=mock_find_user),
    ):
        report = await service.get_class_report("1Q-A", ReportFilter())
    assert report.total_students == 3
    assert len(report.students) == 3
    # média = (70+80+90)/3 = 80
    assert report.avg_accuracy == 80.0


# ── get_teacher_dashboard ─────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_teacher_dashboard_professor_nao_encontrado(service):
    """HTTP 404 quando professor não existe."""
    with patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await service.get_teacher_dashboard("ghost")
    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_teacher_dashboard_sem_alunos(service):
    """Dashboard sem alunos retorna zeros e listas vazias."""
    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=teacher),
        patch.object(service.user_repo, "find_many", new_callable=AsyncMock, return_value=[]),
    ):
        dashboard = await service.get_teacher_dashboard("t001")
    assert dashboard.total_students == 0
    assert dashboard.total_games_today == 0
    assert dashboard.avg_accuracy_this_week == 0.0
    assert dashboard.top_students == []
    assert dashboard.struggling_students == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_teacher_dashboard_identifica_alunos_com_dificuldade(service):
    """Alunos com accuracy < 50% devem estar em struggling_students."""
    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    students = [
        _user("s001"),  # alta accuracy
        _user("s002"),  # baixa accuracy
    ]
    sessions_s001 = [_session("s001", accuracy=90.0, started_at=datetime.utcnow())]
    sessions_s002 = [_session("s002", accuracy=30.0, started_at=datetime.utcnow())]

    async def mock_sessions(uid, limit=50):
        return sessions_s001 if uid == "s001" else sessions_s002

    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=teacher),
        patch.object(service.user_repo, "find_many", new_callable=AsyncMock, return_value=students),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, side_effect=mock_sessions),
    ):
        dashboard = await service.get_teacher_dashboard("t001")
    assert any(s.user_id == "s002" for s in dashboard.struggling_students)
    assert not any(s.user_id == "s001" for s in dashboard.struggling_students)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_teacher_dashboard_top_5_alunos(service):
    """Top students deve conter no máximo 5 alunos, ordenados por accuracy desc."""
    teacher = _user("t001", role=UserRole.PROFESSOR, class_name=None)
    students = [_user(f"s{i:03d}") for i in range(8)]
    accuracies = [95, 85, 75, 65, 55, 45, 35, 25]

    async def mock_sessions(uid, limit=50):
        idx = int(uid[1:])
        return [_session(uid, accuracy=float(accuracies[idx]),
                         started_at=datetime.utcnow())]

    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=teacher),
        patch.object(service.user_repo, "find_many", new_callable=AsyncMock, return_value=students),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock, side_effect=mock_sessions),
    ):
        dashboard = await service.get_teacher_dashboard("t001")
    assert len(dashboard.top_students) <= 5
    if len(dashboard.top_students) >= 2:
        assert dashboard.top_students[0].avg_accuracy >= dashboard.top_students[1].avg_accuracy


# ── Cobertura extra: filtro date_to ───────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_student_report_filtro_date_to(service):
    """date_to deve excluir sessões após a data limite."""
    from datetime import timedelta
    student = _user("s_dt")
    now = datetime.utcnow()
    old_session = _session(student.id, accuracy=80.0, started_at=now - timedelta(days=5))
    recent_session = _session(student.id, accuracy=60.0, started_at=now)

    with (
        patch.object(service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=student),
        patch.object(service.quiz_repo, "find_by_user", new_callable=AsyncMock,
                     return_value=[old_session, recent_session]),
    ):
        from app.schemas.report import ReportFilter
        cutoff = now - timedelta(days=2)
        report = await service.get_student_report(
            "s_dt", ReportFilter(date_to=cutoff)
        )
    # Apenas old_session passou pelo filtro date_to
    assert report.total_games == 1
    assert abs(report.avg_accuracy - 80.0) < 0.01
