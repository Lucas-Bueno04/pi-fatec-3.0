import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.core.config import settings
from app.models.user import User, UserRole, LGPDConsent, UserProgress
from app.models.question import Question, Alternative, DifficultyLevel, QuestionType
from app.security.password import hash_password
from app.security.jwt import create_access_token


TEST_DB_NAME = "labquiz_test"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_student() -> User:
    return User(
        _id="507f1f77bcf86cd799439011",
        name="Ana Silva",
        email="ana@etec.sp.gov.br",
        hashed_password=hash_password("senha123"),
        role=UserRole.ALUNO,
        class_name="1Q-A",
        lgpd_consent=LGPDConsent(accepted=True),
        progress=UserProgress(),
    )


@pytest.fixture
def sample_teacher() -> User:
    return User(
        _id="507f1f77bcf86cd799439012",
        name="Prof. João Santos",
        email="joao@etec.sp.gov.br",
        hashed_password=hash_password("senha123"),
        role=UserRole.PROFESSOR,
        lgpd_consent=LGPDConsent(accepted=True),
    )


@pytest.fixture
def sample_admin() -> User:
    return User(
        _id="507f1f77bcf86cd799439013",
        name="Admin",
        email="admin@etec.sp.gov.br",
        hashed_password=hash_password("senha123"),
        role=UserRole.ADMINISTRADOR,
        lgpd_consent=LGPDConsent(accepted=True),
    )


@pytest.fixture
def student_token(sample_student) -> str:
    return create_access_token({"sub": sample_student.id, "role": sample_student.role.value})


@pytest.fixture
def teacher_token(sample_teacher) -> str:
    return create_access_token({"sub": sample_teacher.id, "role": sample_teacher.role.value})


@pytest.fixture
def sample_question() -> Question:
    alts = [
        Alternative(id="a1", text="Béquer", is_correct=True, alt_text="Béquer de vidro cilíndrico"),
        Alternative(id="a2", text="Erlenmyer", is_correct=False, alt_text="Frasco Erlenmyer"),
        Alternative(id="a3", text="Proveta", is_correct=False, alt_text="Proveta graduada"),
        Alternative(id="a4", text="Funil", is_correct=False, alt_text="Funil de vidro"),
    ]
    return Question(
        _id="507f1f77bcf86cd799439020",
        type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL,
        text="Qual material é utilizado para aquecer substâncias diretamente na chama?",
        alternatives=alts,
        correct_alternative_id="a1",
        explanation="O béquer é resistente ao calor e amplamente usado para aquecimento.",
        material_name="Béquer",
        created_by="507f1f77bcf86cd799439012",
    )
