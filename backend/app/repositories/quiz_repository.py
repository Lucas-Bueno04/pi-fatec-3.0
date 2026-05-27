from typing import List, Optional
from .base import BaseRepository
from ..models.quiz import QuizSession, QuizStatus


class QuizRepository(BaseRepository[QuizSession]):
    collection_name = "quiz_sessions"
    model_class = QuizSession

    async def create_session(self, session: QuizSession) -> QuizSession:
        return await self.create(session.to_mongo())

    async def update_session(self, session_id: str, data: dict) -> Optional[QuizSession]:
        return await self.update(session_id, data)

    async def find_by_user(self, user_id: str, limit: int = 20) -> List[QuizSession]:
        return await self.find_many(
            {"user_id": user_id},
            limit=limit,
            sort=[("started_at", -1)],
        )

    async def find_active_session(self, user_id: str) -> Optional[QuizSession]:
        return await self.find_one({"user_id": user_id, "status": QuizStatus.IN_PROGRESS.value})

    async def get_stats_by_user(self, user_id: str) -> dict:
        pipeline = [
            {"$match": {"user_id": user_id, "status": QuizStatus.COMPLETED.value}},
            {
                "$group": {
                    "_id": "$level",
                    "count": {"$sum": 1},
                    "avg_accuracy": {"$avg": "$accuracy_percent"},
                    "best_accuracy": {"$max": "$accuracy_percent"},
                    "total_score": {"$sum": "$score"},
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=10)
        return {r["_id"]: r for r in results}
