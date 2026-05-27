import uuid
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from loguru import logger

from ..core.config import settings
from ..models.question import Question, Alternative
from ..repositories.question_repository import QuestionRepository
from ..schemas.question import QuestionCreate, QuestionResponse, QuestionFilter, QuestionUpdate


class QuestionService:
    def __init__(self, db):
        self.question_repo = QuestionRepository(db)
        self.db = db

    async def create_question(self, data: QuestionCreate, created_by: str) -> QuestionResponse:
        alternatives = [
            Alternative(**a.model_dump())
            for a in data.alternatives
        ]
        correct_id = next((a.id for a in data.alternatives if a.is_correct), None)

        question = Question(
            type=data.type,
            difficulty=data.difficulty,
            text=data.text,
            image_alt_text=data.image_alt_text,
            alternatives=alternatives,
            correct_alternative_id=correct_id,
            explanation=data.explanation,
            material_name=data.material_name,
            function_text=data.function_text,
            system_name=data.system_name,
            created_by=created_by,
        )

        created = await self.question_repo.create_question(question)
        logger.info(f"Questão criada: {created.id} por {created_by}")
        return self._to_response(created)

    async def upload_image(self, question_id: str, file: UploadFile, field: str = "question") -> str:
        from ..core.database import get_gridfs
        from bson import ObjectId
        gridfs = get_gridfs()
        content = await file.read()
        file_id = await gridfs.upload_from_stream(
            filename=f"{question_id}_{field}_{file.filename}",
            source=content,
            metadata={"question_id": question_id, "field": field, "content_type": file.content_type},
        )
        image_id = str(file_id)

        # Auto-update question document with the new image reference
        if field == "question":
            await self.question_repo.update_question(question_id, {"image_id": image_id})
        elif field.startswith("alt_"):
            alt_idx = int(field.split("_")[1])
            question = await self.question_repo.find_by_id(question_id)
            if question and alt_idx < len(question.alternatives):
                alts = [a.model_dump() for a in question.alternatives]
                alts[alt_idx]["image_id"] = image_id
                await self.question_repo.update_question(question_id, {"alternatives": alts})

        return image_id

    async def get_image(self, image_id: str) -> bytes:
        from ..core.database import get_gridfs
        from bson import ObjectId
        gridfs = get_gridfs()
        try:
            stream = await gridfs.open_download_stream(ObjectId(image_id))
            return await stream.read()
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Imagem não encontrada.")

    async def list_questions(self, f: QuestionFilter, skip: int = 0, limit: int = 50) -> List[QuestionResponse]:
        questions = await self.question_repo.find_filtered(
            q_type=f.type, difficulty=f.difficulty, is_active=f.is_active, skip=skip, limit=limit
        )
        return [self._to_response(q) for q in questions]

    async def get_question(self, question_id: str) -> QuestionResponse:
        q = await self.question_repo.find_by_id(question_id)
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada.")
        return self._to_response(q)

    async def update_question(self, question_id: str, data: QuestionUpdate) -> QuestionResponse:
        update_data = data.model_dump(exclude_none=True)
        if "alternatives" in update_data:
            update_data["alternatives"] = [
                Alternative(**a).model_dump() if isinstance(a, dict) else a.model_dump()
                for a in data.alternatives
            ]
        updated = await self.question_repo.update_question(question_id, update_data)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada.")
        return self._to_response(updated)

    async def delete_question(self, question_id: str) -> None:
        result = await self.question_repo.soft_delete(question_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada.")

    def _to_response(self, q: Question) -> QuestionResponse:
        from ..schemas.question import AlternativeResponse
        return QuestionResponse(
            id=q.id,
            type=q.type,
            difficulty=q.difficulty,
            text=q.text,
            image_id=q.image_id,
            image_url=f"/api/v1/questions/{q.id}/image" if q.image_id else None,
            image_alt_text=q.image_alt_text,
            alternatives=[
                AlternativeResponse(
                    id=a.id,
                    text=a.text,
                    image_id=a.image_id,
                    alt_text=a.alt_text,
                )
                for a in q.alternatives
            ],
            explanation=q.explanation,
            material_name=q.material_name,
            function_text=q.function_text,
            system_name=q.system_name,
            is_active=q.is_active,
            created_by=q.created_by,
        )
