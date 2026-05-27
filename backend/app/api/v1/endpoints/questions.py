from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response

from ....core.database import get_database
from ....models.question import QuestionType, DifficultyLevel
from ....models.user import UserRole
from ....schemas.question import QuestionCreate, QuestionResponse, QuestionUpdate, QuestionFilter
from ....services.question_service import QuestionService
from ....security.jwt import get_current_active_user, require_role

router = APIRouter(prefix="/questions", tags=["Questões"])

_teacher_or_admin = require_role(UserRole.PROFESSOR, UserRole.ADMINISTRADOR)


@router.get("/", response_model=list[QuestionResponse])
async def list_questions(
    type: Optional[QuestionType] = Query(None),
    difficulty: Optional[DifficultyLevel] = Query(None),
    is_active: Optional[bool] = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Lista questões com filtros opcionais."""
    service = QuestionService(db)
    return await service.list_questions(
        QuestionFilter(type=type, difficulty=difficulty, is_active=is_active),
        skip=skip,
        limit=limit,
    )


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    _=Depends(get_current_active_user),
    db=Depends(get_database),
):
    service = QuestionService(db)
    return await service.get_question(question_id)


@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    data: QuestionCreate,
    current_user=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    """Cria nova questão. Apenas professores e administradores."""
    service = QuestionService(db)
    return await service.create_question(data, created_by=current_user.id)


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    data: QuestionUpdate,
    _=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    service = QuestionService(db)
    return await service.update_question(question_id, data)


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    _=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    service = QuestionService(db)
    await service.delete_question(question_id)


@router.post("/{question_id}/image", response_model=dict)
async def upload_image(
    question_id: str,
    file: UploadFile = File(...),
    field: str = Query("question", pattern=r"^(question|alt_[0-9]+)$"),
    _=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    """Faz upload de imagem para uma questão via GridFS."""
    service = QuestionService(db)
    image_id = await service.upload_image(question_id, file, field)
    return {"image_id": image_id}


@router.get("/{question_id}/image")
async def get_image(
    question_id: str,
    field: str = Query("question", pattern=r"^(question|alt_[0-9]+)$"),
    _=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Retorna imagem da questão ou de uma alternativa do GridFS.

    - `field=question` (padrão): imagem principal da questão
    - `field=alt_0`, `alt_1`, ...: imagem da alternativa pelo índice
    """
    from fastapi import HTTPException
    from ....repositories.question_repository import QuestionRepository
    repo = QuestionRepository(db)
    q = await repo.find_by_id(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")

    image_id: Optional[str] = None
    if field == "question":
        image_id = q.image_id
    else:
        alt_idx = int(field.split("_")[1])
        if alt_idx < len(q.alternatives):
            image_id = q.alternatives[alt_idx].image_id

    if not image_id:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    service = QuestionService(db)
    content = await service.get_image(image_id)
    return Response(content=content, media_type="image/jpeg")
