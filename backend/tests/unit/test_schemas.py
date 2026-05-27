"""
=============================================================================
LABQUIZ ETEC — Testes unitários: Validação de Schemas (Pydantic)
=============================================================================
Cobre:
  - LGPDConsentCreate: accepted obrigatório
  - UserCreate: senha mínima 8 chars, turma obrigatória para ALUNO, role
  - QuestionCreate: MULTIPLA_ESCOLHA 4 alts + 1 correta, associação ≥2 pares
  - QuestionUpdate: campos opcionais
  - UserUpdate: campos opcionais
=============================================================================
"""
import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, LGPDConsentCreate, UserUpdate
from app.schemas.question import QuestionCreate, AlternativeCreate, AssociationPairCreate
from app.models.user import UserRole
from app.models.question import QuestionType, DifficultyLevel


# ── LGPDConsentCreate ─────────────────────────────────────────────────────────

@pytest.mark.unit
def test_lgpd_aceito_true_valido():
    consent = LGPDConsentCreate(accepted=True)
    assert consent.accepted is True


@pytest.mark.unit
def test_lgpd_nao_aceito_lanca_validation_error():
    with pytest.raises(ValidationError):
        LGPDConsentCreate(accepted=False)


@pytest.mark.unit
def test_lgpd_com_guardian_name():
    consent = LGPDConsentCreate(accepted=True, guardian_name="Maria Silva")
    assert consent.guardian_name == "Maria Silva"


@pytest.mark.unit
def test_lgpd_guardian_name_opcional():
    consent = LGPDConsentCreate(accepted=True)
    assert consent.guardian_name is None


# ── UserCreate ────────────────────────────────────────────────────────────────

def _base_aluno(**kwargs):
    defaults = dict(
        name="Ana Silva",
        email="ana@etec.sp.gov.br",
        password="senha@123",
        role=UserRole.ALUNO,
        class_name="1Q-A",
        lgpd_consent=LGPDConsentCreate(accepted=True),
    )
    defaults.update(kwargs)
    return defaults


@pytest.mark.unit
def test_user_create_aluno_valido():
    user = UserCreate(**_base_aluno())
    assert user.email == "ana@etec.sp.gov.br"
    assert user.role == UserRole.ALUNO


@pytest.mark.unit
def test_user_create_senha_curta_lanca_erro():
    """Senha menor que 8 caracteres deve ser rejeitada."""
    with pytest.raises(ValidationError):
        UserCreate(**_base_aluno(password="123"))


@pytest.mark.unit
def test_user_create_senha_exatamente_8_chars_aceita():
    user = UserCreate(**_base_aluno(password="12345678"))
    assert user.password == "12345678"


@pytest.mark.unit
def test_user_create_aluno_sem_turma_lanca_erro():
    """ALUNO sem class_name deve ser rejeitado."""
    with pytest.raises(ValidationError):
        UserCreate(**_base_aluno(class_name=None))


@pytest.mark.unit
def test_user_create_professor_sem_turma_valido():
    """PROFESSOR não precisa de class_name."""
    user = UserCreate(
        name="Prof Santos",
        email="prof@etec.sp.gov.br",
        password="senha@123",
        role=UserRole.PROFESSOR,
        class_name=None,
        lgpd_consent=LGPDConsentCreate(accepted=True),
    )
    assert user.role == UserRole.PROFESSOR
    assert user.class_name is None


@pytest.mark.unit
def test_user_create_email_invalido_lanca_erro():
    with pytest.raises(ValidationError):
        UserCreate(**_base_aluno(email="nao-e-um-email"))


@pytest.mark.unit
def test_user_create_role_padrao_e_aluno():
    user = UserCreate(
        name="Novo", email="novo@etec.sp",
        password="senha@123", class_name="1Q-A",
        lgpd_consent=LGPDConsentCreate(accepted=True),
    )
    assert user.role == UserRole.ALUNO


# ── QuestionCreate ────────────────────────────────────────────────────────────

def _four_alts(correct_idx=0):
    return [
        AlternativeCreate(id=f"a{i+1}", text=f"Alt {i+1}", is_correct=(i == correct_idx))
        for i in range(4)
    ]


@pytest.mark.unit
def test_question_create_multipla_escolha_valida():
    q = QuestionCreate(
        type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL,
        text="Qual material mede volume?",
        alternatives=_four_alts(0),
        explanation="A proveta.",
    )
    assert q.type == QuestionType.MULTIPLA_ESCOLHA
    assert len(q.alternatives) == 4


@pytest.mark.unit
def test_question_create_menos_de_4_alternativas_lanca_erro():
    with pytest.raises(ValidationError):
        QuestionCreate(
            type=QuestionType.MULTIPLA_ESCOLHA,
            difficulty=DifficultyLevel.FACIL,
            text="X",
            alternatives=_four_alts()[:3],  # apenas 3
        )


@pytest.mark.unit
def test_question_create_zero_alternativas_corretas_lanca_erro():
    alts = [AlternativeCreate(id=f"a{i}", text=f"X{i}", is_correct=False) for i in range(4)]
    with pytest.raises(ValidationError):
        QuestionCreate(
            type=QuestionType.MULTIPLA_ESCOLHA,
            difficulty=DifficultyLevel.FACIL,
            text="X",
            alternatives=alts,
        )


@pytest.mark.unit
def test_question_create_duas_alternativas_corretas_lanca_erro():
    alts = [
        AlternativeCreate(id="a1", text="A", is_correct=True),
        AlternativeCreate(id="a2", text="B", is_correct=True),
        AlternativeCreate(id="a3", text="C", is_correct=False),
        AlternativeCreate(id="a4", text="D", is_correct=False),
    ]
    with pytest.raises(ValidationError):
        QuestionCreate(
            type=QuestionType.MULTIPLA_ESCOLHA,
            difficulty=DifficultyLevel.FACIL,
            text="X",
            alternatives=alts,
        )


@pytest.mark.unit
def test_question_create_associacao_com_2_pares_valida():
    pairs = [
        AssociationPairCreate(material_id="m1", material_name="Béquer",
                              target_id="t1", target_text="Aquece"),
        AssociationPairCreate(material_id="m2", material_name="Proveta",
                              target_id="t2", target_text="Mede"),
    ]
    q = QuestionCreate(
        type=QuestionType.ASSOCIACAO_FUNCAO,
        difficulty=DifficultyLevel.MEDIO,
        text="Associe.",
        association_pairs=pairs,
        explanation="x",
    )
    assert len(q.association_pairs) == 2


@pytest.mark.unit
def test_question_create_associacao_com_1_par_lanca_erro():
    pairs = [
        AssociationPairCreate(material_id="m1", material_name="X",
                              target_id="t1", target_text="Y"),
    ]
    with pytest.raises(ValidationError):
        QuestionCreate(
            type=QuestionType.ASSOCIACAO_FUNCAO,
            difficulty=DifficultyLevel.MEDIO,
            text="Associe.",
            association_pairs=pairs,
        )


# ── UserUpdate ────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_user_update_todos_none():
    u = UserUpdate()
    assert u.name is None
    assert u.class_name is None
    assert u.is_active is None


@pytest.mark.unit
def test_user_update_parcial():
    u = UserUpdate(name="Novo Nome")
    assert u.name == "Novo Nome"
    assert u.class_name is None
