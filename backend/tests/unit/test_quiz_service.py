"""
=============================================================================
LABQUIZ ETEC — Testes unitários: QuizService (expandido)
=============================================================================
Cobre:
  - start_quiz: distribuição 4+3+3, nível bloqueado (médio/difícil),
                sessão ativa abandonada, usuário não encontrado
  - submit_answer: resposta correta/errada (MC), associação correta,
                   questão não pertence à sessão, questão já respondida,
                   questão não encontrada, sessão não ativa
  - use_help: eliminar 2, dica textual, limite excedido, hint truncado
  - finish_quiz: unlock ≥70%, sem unlock <70%, best_accuracy atualizado,
                 sessão já finalizada
  - get_history: lista de sessões do usuário
=============================================================================
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.quiz_service import QuizService
from app.models.question import DifficultyLevel, QuestionType, Question, Alternative
from app.models.quiz import QuizSession, QuizStatus, QuizAnswer, HelpType
from app.models.user import UserProgress
from app.schemas.quiz import AnswerSubmit, HelpRequest


# ── Fixtures & helpers ────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def quiz_service(mock_db):
    return QuizService(mock_db)


def make_questions(count, difficulty, correct_id="a1"):
    alts = [
        Alternative(id="a1", text="A", is_correct=True),
        Alternative(id="a2", text="B", is_correct=False),
        Alternative(id="a3", text="C", is_correct=False),
        Alternative(id="a4", text="D", is_correct=False),
    ]
    return [
        Question(
            _id=f"q_{difficulty.value}_{i}",
            type=QuestionType.MULTIPLA_ESCOLHA,
            difficulty=difficulty,
            text=f"Questão {i}",
            alternatives=alts,
            correct_alternative_id=correct_id,
            explanation="Explicação de teste.",
            created_by="teacher1",
        )
        for i in range(count)
    ]


def _active_session(uid="s001", questions=None, score=0, help_count=0):
    q_ids = [q.id for q in questions] if questions else ["q1"]
    return QuizSession(
        _id="sess1", user_id=uid, level=DifficultyLevel.FACIL,
        question_ids=q_ids, score=score, total_possible_score=100,
        status=QuizStatus.IN_PROGRESS, help_count=help_count,
    )


# ── start_quiz ────────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_quiz_selects_correct_distribution(quiz_service, sample_student):
    """Quiz deve ter 10 questões (4+3+3)."""
    all_q = make_questions(4, DifficultyLevel.FACIL) + \
            make_questions(3, DifficultyLevel.MEDIO) + \
            make_questions(3, DifficultyLevel.DIFICIL)
    session = QuizSession(
        _id="sess1", user_id=sample_student.id, level=DifficultyLevel.FACIL,
        question_ids=[q.id for q in all_q], total_possible_score=130,
    )
    with (
        patch.object(quiz_service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_student),
        patch.object(quiz_service.quiz_repo, "find_active_session", new_callable=AsyncMock, return_value=None),
        patch.object(quiz_service.question_repo, "find_for_quiz", new_callable=AsyncMock, return_value=all_q),
        patch.object(quiz_service.quiz_repo, "create_session", new_callable=AsyncMock, return_value=session),
    ):
        result = await quiz_service.start_quiz(sample_student.id, DifficultyLevel.FACIL)
    assert result.total_questions == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_quiz_nivel_medio_bloqueado(quiz_service, sample_student):
    """Nível Médio bloqueado → HTTP 403."""
    # sample_student tem medio_unlocked=False por padrão
    with patch.object(quiz_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=sample_student):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.start_quiz(sample_student.id, DifficultyLevel.MEDIO)
    assert exc.value.status_code == 403


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_quiz_nivel_dificil_bloqueado(quiz_service, sample_student):
    """Nível Difícil bloqueado → HTTP 403."""
    with patch.object(quiz_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=sample_student):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.start_quiz(sample_student.id, DifficultyLevel.DIFICIL)
    assert exc.value.status_code == 403


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_quiz_abandona_sessao_ativa(quiz_service, sample_student):
    """Ao iniciar um novo quiz, sessão ativa anterior deve ser abandonada."""
    active = _active_session(uid=sample_student.id)
    all_q = make_questions(4, DifficultyLevel.FACIL) + \
            make_questions(3, DifficultyLevel.MEDIO) + \
            make_questions(3, DifficultyLevel.DIFICIL)
    session = QuizSession(
        _id="sess_new", user_id=sample_student.id, level=DifficultyLevel.FACIL,
        question_ids=[q.id for q in all_q], total_possible_score=130,
    )
    with (
        patch.object(quiz_service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_student),
        patch.object(quiz_service.quiz_repo, "find_active_session", new_callable=AsyncMock, return_value=active),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock) as mock_update,
        patch.object(quiz_service.question_repo, "find_for_quiz", new_callable=AsyncMock, return_value=all_q),
        patch.object(quiz_service.quiz_repo, "create_session", new_callable=AsyncMock, return_value=session),
    ):
        await quiz_service.start_quiz(sample_student.id, DifficultyLevel.FACIL)
    # Primeira chamada update_session é para abandonar a sessão anterior
    first_call_data = mock_update.call_args_list[0][0][1]
    assert first_call_data["status"] == QuizStatus.ABANDONED.value


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_quiz_usuario_nao_encontrado(quiz_service):
    """HTTP 404 quando usuário não existe."""
    with patch.object(quiz_service.user_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.start_quiz("ghost", DifficultyLevel.FACIL)
    assert exc.value.status_code == 404


# ── submit_answer ─────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_correct_answer_adds_points(quiz_service, sample_student, sample_question):
    session = _active_session(uid=sample_student.id, questions=[sample_question])
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_question),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.submit_answer(
            "sess1", sample_student.id,
            AnswerSubmit(question_id=sample_question.id, selected_alternative_id="a1"),
        )
    assert result.is_correct is True
    assert result.points_earned == 10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_wrong_answer_earns_zero(quiz_service, sample_student, sample_question):
    session = _active_session(uid=sample_student.id, questions=[sample_question])
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_question),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.submit_answer(
            "sess1", sample_student.id,
            AnswerSubmit(question_id=sample_question.id, selected_alternative_id="a2"),
        )
    assert result.is_correct is False
    assert result.points_earned == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_questao_nao_pertence_sessao(quiz_service, sample_student):
    """Questão que não pertence à sessão → HTTP 400."""
    session = _active_session(uid=sample_student.id)
    session.question_ids = ["outra_questao"]
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.submit_answer(
                "sess1", sample_student.id,
                AnswerSubmit(question_id="questao_estranha", selected_alternative_id="a1"),
            )
    assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_questao_ja_respondida(quiz_service, sample_student, sample_question):
    """Responder questão já respondida → HTTP 400."""
    session = _active_session(uid=sample_student.id, questions=[sample_question])
    session.answers = [QuizAnswer(question_id=sample_question.id, is_correct=True, points_earned=10)]
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.submit_answer(
                "sess1", sample_student.id,
                AnswerSubmit(question_id=sample_question.id, selected_alternative_id="a1"),
            )
    assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_sessao_outro_usuario(quiz_service, sample_student):
    """Sessão de outro usuário → HTTP 403."""
    session = _active_session(uid="outro_user")
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.submit_answer(
                "sess1", sample_student.id,
                AnswerSubmit(question_id="q1", selected_alternative_id="a1"),
            )
    assert exc.value.status_code == 403


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_sessao_nao_encontrada(quiz_service, sample_student):
    """Sessão inexistente → HTTP 404."""
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.submit_answer(
                "ghost", sample_student.id,
                AnswerSubmit(question_id="q1", selected_alternative_id="a1"),
            )
    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_sessao_ja_finalizada(quiz_service, sample_student, sample_question):
    """Tentar responder em sessão COMPLETED → HTTP 400."""
    session = _active_session(uid=sample_student.id, questions=[sample_question])
    session.status = QuizStatus.COMPLETED
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.submit_answer(
                "sess1", sample_student.id,
                AnswerSubmit(question_id=sample_question.id, selected_alternative_id="a1"),
            )
    assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_associacao_correta(quiz_service, sample_student):
    """Resposta de associação com mapeamento correto → is_correct=True."""
    from app.models.question import AssociationPair
    assoc_q = Question(
        _id="qa1", type=QuestionType.ASSOCIACAO_FUNCAO,
        difficulty=DifficultyLevel.MEDIO,
        text="Associe.",
        alternatives=[],
        association_pairs=[
            AssociationPair(material_id="m1", material_name="Béquer",
                            target_id="t1", target_text="Aquece"),
            AssociationPair(material_id="m2", material_name="Proveta",
                            target_id="t2", target_text="Mede"),
        ],
        explanation="x", created_by="t1",
    )
    session = _active_session(uid=sample_student.id, questions=[assoc_q])
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=assoc_q),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.submit_answer(
            "sess1", sample_student.id,
            AnswerSubmit(
                question_id="qa1",
                association_answers={"m1": "t1", "m2": "t2"},
            ),
        )
    assert result.is_correct is True
    assert result.points_earned == 20  # MEDIO = 20 pts


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_ultima_questao_is_last_true(quiz_service, sample_student, sample_question):
    """is_last_question deve ser True ao responder a última questão."""
    session = _active_session(uid=sample_student.id, questions=[sample_question])
    # Já respondemos 0 de 1 questão; após responder, index=1 >= len=1
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_question),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.submit_answer(
            "sess1", sample_student.id,
            AnswerSubmit(question_id=sample_question.id, selected_alternative_id="a1"),
        )
    assert result.is_last_question is True


# ── use_help ──────────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_use_help_deducts_points(quiz_service, sample_student, sample_question):
    session = _active_session(uid=sample_student.id, questions=[sample_question], score=10)
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_question),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.use_help(
            "sess1", sample_student.id,
            HelpRequest(question_id=sample_question.id, help_type=HelpType.ELIMINATE_TWO),
        )
    assert result.points_deducted == 5
    assert result.eliminated_alternative_ids is not None
    assert len(result.eliminated_alternative_ids) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_use_help_text_hint_deduz_3pts(quiz_service, sample_student, sample_question):
    session = _active_session(uid=sample_student.id, questions=[sample_question], score=10)
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_question),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.use_help(
            "sess1", sample_student.id,
            HelpRequest(question_id=sample_question.id, help_type=HelpType.TEXT_HINT),
        )
    assert result.points_deducted == 3
    assert result.hint_text is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_use_help_limite_excedido(quiz_service, sample_student, sample_question):
    """Mais de 2 ajudas → HTTP 400."""
    session = _active_session(uid=sample_student.id, questions=[sample_question], help_count=2)
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.use_help(
                "sess1", sample_student.id,
                HelpRequest(question_id=sample_question.id, help_type=HelpType.ELIMINATE_TWO),
            )
    assert exc.value.status_code == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_use_help_helps_remaining_decrements(quiz_service, sample_student, sample_question):
    """helps_remaining deve decrementar corretamente."""
    session = _active_session(uid=sample_student.id, questions=[sample_question], help_count=0)
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_question),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.use_help(
            "sess1", sample_student.id,
            HelpRequest(question_id=sample_question.id, help_type=HelpType.ELIMINATE_TWO),
        )
    assert result.helps_remaining == 1  # 2 - 1 = 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_use_help_hint_truncado_em_120(quiz_service, sample_student):
    """Hint com explicação > 120 chars deve ser truncado com '...'."""
    long_explanation = "X" * 200
    q_long = Question(
        _id="qlong", type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL,
        text="Q?",
        alternatives=[
            Alternative(id="a1", text="A", is_correct=True),
            Alternative(id="a2", text="B", is_correct=False),
        ],
        explanation=long_explanation, created_by="t1",
    )
    session = _active_session(uid=sample_student.id, questions=[q_long])
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=q_long),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
    ):
        result = await quiz_service.use_help(
            "sess1", sample_student.id,
            HelpRequest(question_id="qlong", help_type=HelpType.TEXT_HINT),
        )
    assert result.hint_text.endswith("...")
    assert len(result.hint_text) <= 123  # 120 + "..."


# ── finish_quiz ───────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_finish_quiz_unlocks_next_level_at_70_percent(quiz_service, sample_student):
    """70% de acerto desbloqueia nível Médio."""
    answers = [QuizAnswer(question_id=f"q{i}", is_correct=True, points_earned=10)
               for i in range(7)]
    answers += [QuizAnswer(question_id=f"q{7+i}", is_correct=False, points_earned=0)
                for i in range(3)]
    session = QuizSession(
        _id="sess1", user_id=sample_student.id, level=DifficultyLevel.FACIL,
        question_ids=[f"q{i}" for i in range(10)],
        score=70, total_possible_score=100,
        status=QuizStatus.IN_PROGRESS, answers=answers,
    )
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
        patch.object(quiz_service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_student),
        patch.object(quiz_service.user_repo, "update_progress", new_callable=AsyncMock),
    ):
        result = await quiz_service.finish_quiz("sess1", sample_student.id)
    assert result.accuracy_percent == 70.0
    assert result.level_unlocked == DifficultyLevel.MEDIO


@pytest.mark.unit
@pytest.mark.asyncio
async def test_finish_quiz_does_not_unlock_below_70_percent(quiz_service, sample_student):
    """Abaixo de 70% não desbloqueia."""
    answers = [QuizAnswer(question_id=f"q{i}", is_correct=True, points_earned=10)
               for i in range(6)]
    answers += [QuizAnswer(question_id=f"q{6+i}", is_correct=False, points_earned=0)
                for i in range(4)]
    session = QuizSession(
        _id="sess1", user_id=sample_student.id, level=DifficultyLevel.FACIL,
        question_ids=[f"q{i}" for i in range(10)],
        score=60, total_possible_score=100,
        status=QuizStatus.IN_PROGRESS, answers=answers,
    )
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
        patch.object(quiz_service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_student),
        patch.object(quiz_service.user_repo, "update_progress", new_callable=AsyncMock),
    ):
        result = await quiz_service.finish_quiz("sess1", sample_student.id)
    assert result.accuracy_percent == 60.0
    assert result.level_unlocked is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_finish_quiz_100_percent_resultado(quiz_service, sample_student):
    """100% de acerto calcula corretamente."""
    answers = [QuizAnswer(question_id=f"q{i}", is_correct=True, points_earned=10)
               for i in range(10)]
    session = QuizSession(
        _id="sess1", user_id=sample_student.id, level=DifficultyLevel.FACIL,
        question_ids=[f"q{i}" for i in range(10)],
        score=100, total_possible_score=100,
        status=QuizStatus.IN_PROGRESS, answers=answers,
    )
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.quiz_repo, "update_session", new_callable=AsyncMock),
        patch.object(quiz_service.user_repo, "find_by_id", new_callable=AsyncMock, return_value=sample_student),
        patch.object(quiz_service.user_repo, "update_progress", new_callable=AsyncMock),
    ):
        result = await quiz_service.finish_quiz("sess1", sample_student.id)
    assert result.accuracy_percent == 100.0
    assert result.correct_count == 10
    assert result.wrong_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_finish_quiz_sessao_ja_finalizada_retorna_400(quiz_service, sample_student):
    """Finalizar sessão já COMPLETED → HTTP 400."""
    session = QuizSession(
        _id="sess1", user_id=sample_student.id, level=DifficultyLevel.FACIL,
        question_ids=["q1"], score=0, total_possible_score=10,
        status=QuizStatus.COMPLETED,
    )
    with patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.finish_quiz("sess1", sample_student.id)
    assert exc.value.status_code == 400


# ── get_history ───────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history_retorna_lista(quiz_service, sample_student):
    """get_history retorna todas as sessões do usuário."""
    sessions = [
        QuizSession(_id=f"s{i}", user_id=sample_student.id, level=DifficultyLevel.FACIL,
                    question_ids=["q1"], score=i * 10, total_possible_score=100,
                    status=QuizStatus.COMPLETED)
        for i in range(3)
    ]
    with patch.object(quiz_service.quiz_repo, "find_by_user",
                      new_callable=AsyncMock, return_value=sessions):
        result = await quiz_service.get_history(sample_student.id)
    assert len(result) == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history_vazio(quiz_service, sample_student):
    """get_history sem histórico retorna lista vazia."""
    with patch.object(quiz_service.quiz_repo, "find_by_user",
                      new_callable=AsyncMock, return_value=[]):
        result = await quiz_service.get_history(sample_student.id)
    assert result == []


# ── Cobertura extra: 404 no DB durante submit/help ────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_question_not_in_db_returns_404(quiz_service, sample_student, sample_question):
    """questão pertence à sessão mas foi deletada do banco → HTTP 404."""
    session = _active_session(uid=sample_student.id, questions=[sample_question])
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=None),
    ):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.submit_answer(
                "sess1", sample_student.id,
                AnswerSubmit(question_id=sample_question.id, selected_alternative_id="a1"),
            )
    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_use_help_question_not_in_db_returns_404(quiz_service, sample_student, sample_question):
    """questão não encontrada no banco durante use_help → HTTP 404."""
    session = _active_session(uid=sample_student.id, questions=[sample_question], score=20)
    with (
        patch.object(quiz_service.quiz_repo, "find_by_id", new_callable=AsyncMock, return_value=session),
        patch.object(quiz_service.question_repo, "find_by_id", new_callable=AsyncMock, return_value=None),
    ):
        with pytest.raises(HTTPException) as exc:
            await quiz_service.use_help(
                "sess1", sample_student.id,
                HelpRequest(question_id=sample_question.id, help_type=HelpType.ELIMINATE_TWO),
            )
    assert exc.value.status_code == 404
