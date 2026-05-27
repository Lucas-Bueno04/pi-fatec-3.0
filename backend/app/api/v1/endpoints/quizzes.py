from fastapi import APIRouter, Depends, status

from ....core.database import get_database
from ....models.question import DifficultyLevel
from ....schemas.quiz import (
    QuizStartRequest, AnswerSubmit, HelpRequest,
    HelpResponse, AnswerResult, QuizResultResponse,
    QuizSessionResponse, QuizHistoryResponse,
)
from ....services.quiz_service import QuizService
from ....security.jwt import get_current_active_user

router = APIRouter(prefix="/quizzes", tags=["Quiz"])


@router.post("/start", response_model=QuizSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_quiz(
    data: QuizStartRequest,
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Inicia uma nova sessão de quiz no nível escolhido."""
    service = QuizService(db)
    return await service.start_quiz(current_user.id, data.level)


@router.post("/{session_id}/answer", response_model=AnswerResult)
async def submit_answer(
    session_id: str,
    data: AnswerSubmit,
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Submete a resposta para uma questão da sessão ativa."""
    service = QuizService(db)
    return await service.submit_answer(session_id, current_user.id, data)


@router.post("/{session_id}/help", response_model=HelpResponse)
async def use_help(
    session_id: str,
    data: HelpRequest,
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Usa uma ajuda na sessão ativa. Reduz pontuação."""
    service = QuizService(db)
    return await service.use_help(session_id, current_user.id, data)


@router.post("/{session_id}/finish", response_model=QuizResultResponse)
async def finish_quiz(
    session_id: str,
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Finaliza a sessão de quiz e calcula resultado final."""
    service = QuizService(db)
    return await service.finish_quiz(session_id, current_user.id)


@router.get("/history", response_model=list[QuizSessionResponse])
async def get_history(
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Histórico de quizzes do usuário autenticado."""
    service = QuizService(db)
    return await service.get_history(current_user.id)


@router.get("/{session_id}", response_model=QuizSessionResponse)
async def get_session(
    session_id: str,
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Retorna detalhes de uma sessão específica."""
    from ....repositories.quiz_repository import QuizRepository
    repo = QuizRepository(db)
    session = await repo.find_by_id(session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return QuizSessionResponse(
        id=session.id,
        level=session.level,
        status=session.status,
        score=session.score,
        total_possible_score=session.total_possible_score,
        accuracy_percent=session.accuracy_percent,
        help_count=session.help_count,
        started_at=session.started_at,
        finished_at=session.finished_at,
        current_question_index=session.current_question_index,
        total_questions=len(session.question_ids),
        question_ids=session.question_ids,
    )
