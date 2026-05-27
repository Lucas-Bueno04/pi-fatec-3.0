"""
=============================================================================
LABQUIZ ETEC — Testes unitários: Modelos de domínio
=============================================================================
Cobre:
  - User: to_mongo, from_mongo, roles, progress defaults
  - Question: to_mongo, from_mongo, tipos e dificuldades
  - QuizSession: to_mongo, from_mongo, status enum
  - Alternative / AssociationPair
=============================================================================
"""
import pytest
from datetime import datetime

from app.models.user import User, UserRole, LGPDConsent, UserProgress
from app.models.question import (
    Question, Alternative, AssociationPair,
    QuestionType, DifficultyLevel,
)
from app.models.quiz import QuizSession, QuizAnswer, QuizStatus, HelpType, HelpUsed
from app.security.password import hash_password


# ── User ──────────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_user_criado_com_defaults():
    u = User(
        name="Ana", email="ana@etec.sp",
        hashed_password=hash_password("senha123"),
    )
    assert u.role == UserRole.ALUNO
    assert u.is_active is True
    assert u.progress.facil_unlocked is True
    assert u.progress.medio_unlocked is False
    assert u.progress.dificil_unlocked is False


@pytest.mark.unit
def test_user_to_mongo_nao_contem_id():
    u = User(
        _id="507f1f77bcf86cd799439011",
        name="Ana", email="ana@etec.sp",
        hashed_password="hash",
    )
    data = u.to_mongo()
    assert "_id" not in data
    assert "name" in data
    assert "email" in data


@pytest.mark.unit
def test_user_to_mongo_contem_lgpd_como_dict():
    u = User(
        name="Ana", email="a@b.com",
        hashed_password="h",
        lgpd_consent=LGPDConsent(accepted=True, guardian_name="Maria"),
    )
    data = u.to_mongo()
    assert isinstance(data["lgpd_consent"], dict)
    assert data["lgpd_consent"]["guardian_name"] == "Maria"


@pytest.mark.unit
def test_user_from_mongo_converte_id_para_str():
    from bson import ObjectId
    raw = {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "name": "Ana",
        "email": "a@b.com",
        "hashed_password": "h",
        "role": "ALUNO",
        "is_active": True,
        "lgpd_consent": {"accepted": True},
        "progress": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    u = User.from_mongo(raw)
    assert isinstance(u.id, str)
    assert u.id == "507f1f77bcf86cd799439011"


@pytest.mark.unit
def test_user_roles_enum():
    assert UserRole.ALUNO.value == "ALUNO"
    assert UserRole.PROFESSOR.value == "PROFESSOR"
    assert UserRole.ADMINISTRADOR.value == "ADMINISTRADOR"


@pytest.mark.unit
def test_user_progress_defaults():
    p = UserProgress()
    assert p.facil_unlocked is True
    assert p.medio_unlocked is False
    assert p.dificil_unlocked is False
    assert p.facil_best_accuracy == 0.0


# ── Question ──────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_question_to_mongo_serializa_alternativas():
    alts = [Alternative(id="a1", text="A", is_correct=True)]
    q = Question(
        type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL,
        text="Q?", alternatives=alts,
        correct_alternative_id="a1",
        created_by="t1",
    )
    data = q.to_mongo()
    assert isinstance(data["alternatives"], list)
    assert data["alternatives"][0]["id"] == "a1"


@pytest.mark.unit
def test_question_from_mongo_converte_id():
    from bson import ObjectId
    raw = {
        "_id": ObjectId("507f1f77bcf86cd799439022"),
        "type": "MULTIPLA_ESCOLHA",
        "difficulty": "FACIL",
        "text": "Q?",
        "alternatives": [],
        "association_pairs": [],
        "explanation": "",
        "is_active": True,
        "created_by": "t1",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    q = Question.from_mongo(raw)
    assert q.id == "507f1f77bcf86cd799439022"


@pytest.mark.unit
def test_question_tipos_enum():
    assert QuestionType.MULTIPLA_ESCOLHA.value == "MULTIPLA_ESCOLHA"
    assert QuestionType.ASSOCIACAO_FUNCAO.value == "ASSOCIACAO_FUNCAO"
    assert QuestionType.ASSOCIACAO_SISTEMA.value == "ASSOCIACAO_SISTEMA"


@pytest.mark.unit
def test_question_dificuldades_enum():
    assert DifficultyLevel.FACIL.value == "FACIL"
    assert DifficultyLevel.MEDIO.value == "MEDIO"
    assert DifficultyLevel.DIFICIL.value == "DIFICIL"


@pytest.mark.unit
def test_alternative_is_correct_default_false():
    alt = Alternative(id="a1", text="Texto")
    assert alt.is_correct is False


@pytest.mark.unit
def test_association_pair_campos():
    pair = AssociationPair(
        material_id="m1", material_name="Béquer",
        target_id="t1", target_text="Aquece substâncias",
    )
    assert pair.material_name == "Béquer"
    assert pair.target_text == "Aquece substâncias"


# ── QuizSession ───────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_quiz_session_status_default():
    s = QuizSession(
        user_id="u1", level=DifficultyLevel.FACIL,
        question_ids=["q1"], total_possible_score=10,
    )
    assert s.status == QuizStatus.IN_PROGRESS


@pytest.mark.unit
def test_quiz_session_to_mongo_serializa_answers():
    answer = QuizAnswer(question_id="q1", is_correct=True, points_earned=10)
    s = QuizSession(
        user_id="u1", level=DifficultyLevel.FACIL,
        question_ids=["q1"], answers=[answer],
    )
    data = s.to_mongo()
    assert isinstance(data["answers"], list)
    assert data["answers"][0]["question_id"] == "q1"


@pytest.mark.unit
def test_quiz_session_from_mongo_converte_id():
    from bson import ObjectId
    raw = {
        "_id": ObjectId("507f1f77bcf86cd799439033"),
        "user_id": "u1",
        "level": "FACIL",
        "question_ids": [],
        "current_question_index": 0,
        "answers": [],
        "score": 0,
        "total_possible_score": 100,
        "accuracy_percent": 0.0,
        "help_count": 0,
        "status": "IN_PROGRESS",
        "started_at": datetime.utcnow(),
    }
    s = QuizSession.from_mongo(raw)
    assert s.id == "507f1f77bcf86cd799439033"


@pytest.mark.unit
def test_quiz_status_enum():
    assert QuizStatus.IN_PROGRESS.value == "IN_PROGRESS"
    assert QuizStatus.COMPLETED.value == "COMPLETED"
    assert QuizStatus.ABANDONED.value == "ABANDONED"


@pytest.mark.unit
def test_help_type_enum():
    assert HelpType.ELIMINATE_TWO.value == "ELIMINATE_TWO"
    assert HelpType.TEXT_HINT.value == "TEXT_HINT"


@pytest.mark.unit
def test_quiz_answer_defaults():
    a = QuizAnswer(question_id="q1")
    assert a.is_correct is False
    assert a.points_earned == 0
    assert a.helps_used == []
