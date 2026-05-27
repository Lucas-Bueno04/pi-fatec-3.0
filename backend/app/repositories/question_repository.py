import random
from datetime import datetime
from typing import List, Optional
from .base import BaseRepository
from ..models.question import Question, DifficultyLevel, QuestionType


class QuestionRepository(BaseRepository[Question]):
    collection_name = "questions"
    model_class = Question

    async def find_by_difficulty(self, difficulty: DifficultyLevel, active_only: bool = True) -> List[Question]:
        f = {"difficulty": difficulty.value}
        if active_only:
            f["is_active"] = True
        return await self.find_many(f, limit=500)

    async def find_for_quiz(self, easy_n: int, medium_n: int, hard_n: int) -> List[Question]:
        easy = await self.find_by_difficulty(DifficultyLevel.FACIL)
        medium = await self.find_by_difficulty(DifficultyLevel.MEDIO)
        hard = await self.find_by_difficulty(DifficultyLevel.DIFICIL)

        if len(easy) < easy_n or len(medium) < medium_n or len(hard) < hard_n:
            raise ValueError(
                f"Questões insuficientes no banco. "
                f"Necessário: {easy_n} fácil, {medium_n} médio, {hard_n} difícil. "
                f"Disponível: {len(easy)} fácil, {len(medium)} médio, {len(hard)} difícil."
            )

        selected = (
            random.sample(easy, easy_n)
            + random.sample(medium, medium_n)
            + random.sample(hard, hard_n)
        )
        random.shuffle(selected)
        return selected

    async def create_question(self, question: Question) -> Question:
        data = question.to_mongo()
        return await self.create(data)

    async def update_question(self, question_id: str, data: dict) -> Optional[Question]:
        data["updated_at"] = datetime.utcnow()
        return await self.update(question_id, data)

    async def soft_delete(self, question_id: str) -> Optional[Question]:
        return await self.update(question_id, {"is_active": False, "updated_at": datetime.utcnow()})

    async def find_filtered(
        self,
        q_type: Optional[QuestionType] = None,
        difficulty: Optional[DifficultyLevel] = None,
        is_active: Optional[bool] = True,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Question]:
        f = {}
        if q_type:
            f["type"] = q_type.value
        if difficulty:
            f["difficulty"] = difficulty.value
        if is_active is not None:
            f["is_active"] = is_active
        return await self.find_many(f, skip=skip, limit=limit)
