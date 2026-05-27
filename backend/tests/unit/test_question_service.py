"""
=============================================================================
LABQUIZ ETEC — Testes unitários: QuestionService
=============================================================================
Cobre:
  - create_question (múltipla escolha e associação)
  - list_questions (sem filtro e com filtros)
  - get_question (encontrado e não encontrado)
  - update_question (sucesso e não encontrado)
  - delete_question (sucesso e não encontrado)
  - _to_response (conversão modelo → schema)
=============================================================================
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.question_service import QuestionService
from app.models.question import Question, Alternative, AssociationPair, QuestionType, DifficultyLevel
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionFilter,
    AlternativeCreate, AssociationPairCreate,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return QuestionService(mock_db)


def _make_mc_question(qid="q001", diff=DifficultyLevel.FACIL):
    return Question(
        _id=qid,
        type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=diff,
        text="Qual vidraria mede volume com precisão?",
        alternatives=[
            Alternative(id="a1", text="Proveta", is_correct=True, alt_text="Proveta graduada"),
            Alternative(id="a2", text="Béquer", is_correct=False, alt_text="Béquer"),
            Alternative(id="a3", text="Funil", is_correct=False, alt_text="Funil"),
            Alternative(id="a4", text="Bastão", is_correct=False, alt_text="Bastão de vidro"),
        ],
        correct_alternative_id="a1",
        explanation="A proveta possui escala graduada para medição precisa.",
        material_name="Proveta",
        created_by="teacher01",
    )


def _make_assoc_question(qid="q002"):
    return Question(
        _id=qid,
        type=QuestionType.ASSOCIACAO_FUNCAO,
        difficulty=DifficultyLevel.MEDIO,
        text="Associe o material à sua função.",
        alternatives=[],
        association_pairs=[
            AssociationPair(material_id="m1", material_name="Béquer",
                            target_id="t1", target_text="Aquecer substâncias"),
            AssociationPair(material_id="m2", material_name="Proveta",
                            target_id="t2", target_text="Medir volume"),
        ],
        explanation="Béquer aquece, proveta mede.",
        created_by="teacher01",
    )


def _mc_create_data():
    return QuestionCreate(
        type=QuestionType.MULTIPLA_ESCOLHA,
        difficulty=DifficultyLevel.FACIL,
        text="Qual vidraria mede volume com precisão?",
        alternatives=[
            AlternativeCreate(id="a1", text="Proveta", is_correct=True, alt_text="Proveta"),
            AlternativeCreate(id="a2", text="Béquer", is_correct=False),
            AlternativeCreate(id="a3", text="Funil", is_correct=False),
            AlternativeCreate(id="a4", text="Bastão", is_correct=False),
        ],
        explanation="A proveta possui escala graduada.",
        material_name="Proveta",
    )


# ── create_question ───────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_question_multipla_escolha_sucesso(service):
    """Criação bem-sucedida de questão múltipla escolha."""
    expected = _make_mc_question()
    with patch.object(service.question_repo, "create_question",
                      new_callable=AsyncMock, return_value=expected):
        result = await service.create_question(_mc_create_data(), created_by="teacher01")
    assert result.type == QuestionType.MULTIPLA_ESCOLHA
    assert result.difficulty == DifficultyLevel.FACIL
    assert result.text == "Qual vidraria mede volume com precisão?"
    assert len(result.alternatives) == 4


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_question_sets_created_by(service):
    """created_by deve ser propagado corretamente."""
    expected = _make_mc_question()
    with patch.object(service.question_repo, "create_question",
                      new_callable=AsyncMock, return_value=expected):
        result = await service.create_question(_mc_create_data(), created_by="teacher01")
    assert result.created_by == "teacher01"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_question_identificica_correct_alternative_id(service):
    """O correct_alternative_id deve ser o ID da alternativa marcada como correta."""
    expected = _make_mc_question()
    with patch.object(service.question_repo, "create_question",
                      new_callable=AsyncMock, return_value=expected):
        result = await service.create_question(_mc_create_data(), created_by="teacher01")
    # a1 é a correta
    assert any(a.id == "a1" for a in result.alternatives)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_question_associacao_sucesso(service):
    """Criação de questão de associação de função."""
    expected = _make_assoc_question()
    data = QuestionCreate(
        type=QuestionType.ASSOCIACAO_FUNCAO,
        difficulty=DifficultyLevel.MEDIO,
        text="Associe o material à sua função.",
        association_pairs=[
            AssociationPairCreate(material_id="m1", material_name="Béquer",
                                  target_id="t1", target_text="Aquecer substâncias"),
            AssociationPairCreate(material_id="m2", material_name="Proveta",
                                  target_id="t2", target_text="Medir volume"),
        ],
        explanation="Béquer aquece, proveta mede.",
    )
    with patch.object(service.question_repo, "create_question",
                      new_callable=AsyncMock, return_value=expected):
        result = await service.create_question(data, created_by="teacher01")
    assert result.type == QuestionType.ASSOCIACAO_FUNCAO


# ── list_questions ────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_questions_sem_filtro(service):
    """Listar sem filtros retorna todas as questões ativas."""
    questions = [_make_mc_question(f"q{i}") for i in range(5)]
    with patch.object(service.question_repo, "find_filtered",
                      new_callable=AsyncMock, return_value=questions):
        result = await service.list_questions(QuestionFilter(), skip=0, limit=50)
    assert len(result) == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_questions_com_filtro_dificuldade(service):
    """Filtro por dificuldade deve ser passado ao repositório."""
    questions = [_make_mc_question(f"q{i}", diff=DifficultyLevel.MEDIO) for i in range(3)]
    with patch.object(service.question_repo, "find_filtered",
                      new_callable=AsyncMock, return_value=questions) as mock_find:
        result = await service.list_questions(
            QuestionFilter(difficulty=DifficultyLevel.MEDIO), skip=0, limit=50
        )
    mock_find.assert_called_once_with(
        q_type=None, difficulty=DifficultyLevel.MEDIO,
        is_active=True, skip=0, limit=50
    )
    assert len(result) == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_questions_vazio(service):
    """Lista vazia retorna lista Python vazia."""
    with patch.object(service.question_repo, "find_filtered",
                      new_callable=AsyncMock, return_value=[]):
        result = await service.list_questions(QuestionFilter())
    assert result == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_questions_filtro_tipo(service):
    """Filtro por tipo MULTIPLA_ESCOLHA deve ser repassado."""
    q = _make_mc_question()
    with patch.object(service.question_repo, "find_filtered",
                      new_callable=AsyncMock, return_value=[q]) as mock_find:
        await service.list_questions(
            QuestionFilter(type=QuestionType.MULTIPLA_ESCOLHA)
        )
    mock_find.assert_called_once_with(
        q_type=QuestionType.MULTIPLA_ESCOLHA, difficulty=None,
        is_active=True, skip=0, limit=50
    )


# ── get_question ──────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_question_encontrado(service):
    """get_question retorna resposta quando questão existe."""
    q = _make_mc_question()
    with patch.object(service.question_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=q):
        result = await service.get_question("q001")
    assert result.id == "q001"
    assert result.text == q.text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_question_nao_encontrado(service):
    """get_question lança HTTP 404 quando questão não existe."""
    with patch.object(service.question_repo, "find_by_id",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await service.get_question("inexistente")
    assert exc.value.status_code == 404


# ── update_question ───────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_question_sucesso(service):
    """update_question retorna questão atualizada."""
    updated = _make_mc_question()
    updated.text = "Texto atualizado"
    with patch.object(service.question_repo, "update_question",
                      new_callable=AsyncMock, return_value=updated):
        result = await service.update_question(
            "q001", QuestionUpdate(text="Texto atualizado")
        )
    assert result.text == "Texto atualizado"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_question_nao_encontrado(service):
    """update_question lança HTTP 404 quando repo retorna None."""
    with patch.object(service.question_repo, "update_question",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await service.update_question("ghost", QuestionUpdate(text="X"))
    assert exc.value.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_question_is_active_false(service):
    """Desativar questão (is_active=False) deve ser persistido."""
    q = _make_mc_question()
    q.is_active = False
    with patch.object(service.question_repo, "update_question",
                      new_callable=AsyncMock, return_value=q) as mock_upd:
        await service.update_question("q001", QuestionUpdate(is_active=False))
    call_data = mock_upd.call_args[0][1]
    assert call_data.get("is_active") is False


# ── delete_question ───────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_question_sucesso(service):
    """delete_question (soft delete) retorna sem erro quando questão existe."""
    q = _make_mc_question()
    q.is_active = False
    with patch.object(service.question_repo, "soft_delete",
                      new_callable=AsyncMock, return_value=q):
        await service.delete_question("q001")  # deve completar sem exceção


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_question_nao_encontrado(service):
    """delete_question lança HTTP 404 quando soft_delete retorna None."""
    with patch.object(service.question_repo, "soft_delete",
                      new_callable=AsyncMock, return_value=None):
        with pytest.raises(HTTPException) as exc:
            await service.delete_question("ghost")
    assert exc.value.status_code == 404


# ── _to_response (image_url) ──────────────────────────────────────────────────

@pytest.mark.unit
def test_to_response_sem_imagem(service):
    """image_url deve ser None quando questão não tem imagem."""
    q = _make_mc_question()
    q.image_id = None
    resp = service._to_response(q)
    assert resp.image_url is None


@pytest.mark.unit
def test_to_response_com_imagem(service):
    """image_url deve ser preenchida com rota correta quando há image_id."""
    q = _make_mc_question()
    q.image_id = "img123"
    resp = service._to_response(q)
    assert resp.image_url == "/api/v1/questions/q001/image"


@pytest.mark.unit
def test_to_response_alternativas_sem_is_correct(service):
    """is_correct NÃO deve aparecer nas alternativas da resposta (ocultado)."""
    q = _make_mc_question()
    resp = service._to_response(q)
    # AlternativeResponse expõe is_correct como Optional — pode ser None no contexto quiz
    for alt in resp.alternatives:
        assert hasattr(alt, "id") and hasattr(alt, "text")


# ── upload_image ──────────────────────────────────────────────────────────────

VALID_QID = "507f1f77bcf86cd799439011"  # 24-char hex ObjectId válido para testes


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_image_retorna_file_id(service):
    """upload_image deve chamar gridfs, atualizar a questão e retornar o id como string."""
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value=b"conteudo_da_imagem")
    mock_file.filename = "imagem.png"
    mock_file.content_type = "image/png"

    fake_id = "507f1f77bcf86cd799439011"
    mock_gridfs = MagicMock()
    mock_gridfs.upload_from_stream = AsyncMock(return_value=fake_id)

    # upload_image agora atualiza a questão após o upload — mockar repo
    service.question_repo.update_question = AsyncMock(return_value=None)

    with patch("app.core.database.get_gridfs", return_value=mock_gridfs):
        result = await service.upload_image(VALID_QID, mock_file, field="question")

    assert result == fake_id
    service.question_repo.update_question.assert_awaited_once_with(
        VALID_QID, {"image_id": fake_id}
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upload_image_com_campo_alt(service):
    """upload_image com field='alt_0' deve atualizar o image_id na alternativa correta."""
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value=b"bytes")
    mock_file.filename = "alt.png"
    mock_file.content_type = "image/png"

    fake_id = "507f1f77bcf86cd799439012"
    mock_gridfs = MagicMock()
    mock_gridfs.upload_from_stream = AsyncMock(return_value=fake_id)

    # Retorna questão com 4 alternativas para o find_by_id do alt branch
    service.question_repo.find_by_id = AsyncMock(return_value=_make_mc_question(qid=VALID_QID))
    service.question_repo.update_question = AsyncMock(return_value=None)

    with patch("app.core.database.get_gridfs", return_value=mock_gridfs):
        result = await service.upload_image(VALID_QID, mock_file, field="alt_0")

    assert result == fake_id
    mock_gridfs.upload_from_stream.assert_called_once()
    # Verifica que update_question foi chamado com a lista de alternativas atualizada
    service.question_repo.update_question.assert_awaited_once()
    call_args = service.question_repo.update_question.call_args
    updated_alts = call_args[0][1]["alternatives"]
    assert updated_alts[0]["image_id"] == fake_id  # alt_0 recebeu o image_id
    call_kw = mock_gridfs.upload_from_stream.call_args.kwargs
    assert call_kw["metadata"]["field"] == "alt_0"


# ── get_image ─────────────────────────────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_image_retorna_bytes(service):
    """get_image deve retornar bytes do stream quando imagem existe."""
    mock_stream = MagicMock()
    mock_stream.read = AsyncMock(return_value=b"imagem_bytes")

    mock_gridfs = MagicMock()
    mock_gridfs.open_download_stream = AsyncMock(return_value=mock_stream)

    with patch("app.core.database.get_gridfs", return_value=mock_gridfs):
        result = await service.get_image("507f1f77bcf86cd799439011")

    assert result == b"imagem_bytes"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_image_nao_encontrada_lanca_404(service):
    """get_image deve lançar HTTP 404 quando o stream lança exceção."""
    mock_gridfs = MagicMock()
    mock_gridfs.open_download_stream = AsyncMock(side_effect=Exception("not found"))

    with patch("app.core.database.get_gridfs", return_value=mock_gridfs):
        with pytest.raises(HTTPException) as exc:
            await service.get_image("507f1f77bcf86cd799439011")

    assert exc.value.status_code == 404
    assert "Imagem não encontrada" in exc.value.detail


# ── update_question com alternatives ─────────────────────────────────────────

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_question_com_alternativas(service):
    """Quando alternatives está no update_data, deve converter para Alternative."""
    from app.schemas.question import AlternativeCreate
    updated = _make_mc_question()
    updated.alternatives = [
        Alternative(id="a1", text="Nova Proveta", is_correct=True),
        Alternative(id="a2", text="Béquer", is_correct=False),
        Alternative(id="a3", text="Funil", is_correct=False),
        Alternative(id="a4", text="Bastão", is_correct=False),
    ]

    update_schema = QuestionUpdate(
        alternatives=[
            AlternativeCreate(id="a1", text="Nova Proveta", is_correct=True),
            AlternativeCreate(id="a2", text="Béquer", is_correct=False),
            AlternativeCreate(id="a3", text="Funil", is_correct=False),
            AlternativeCreate(id="a4", text="Bastão", is_correct=False),
        ]
    )
    with patch.object(service.question_repo, "update_question",
                      new_callable=AsyncMock, return_value=updated):
        result = await service.update_question("q001", update_schema)

    assert len(result.alternatives) == 4
