from datetime import datetime
from typing import List, Optional
from .base import BaseRepository
from ..models.user import User, UserProgress


class UserRepository(BaseRepository[User]):
    collection_name = "users"
    model_class = User

    async def find_by_email(self, email: str) -> Optional[User]:
        return await self.find_one({"email": email})

    async def create_user(self, user: User) -> User:
        data = user.to_mongo()
        return await self.create(data)

    async def update_progress(self, user_id: str, progress: UserProgress) -> Optional[User]:
        return await self.update(user_id, {
            "progress": progress.model_dump(),
            "updated_at": datetime.utcnow(),
        })

    async def list_by_class(self, class_name: str) -> List[User]:
        return await self.find_many({"class_name": class_name, "is_active": True})

    async def update_user(self, user_id: str, data: dict) -> Optional[User]:
        data["updated_at"] = datetime.utcnow()
        return await self.update(user_id, data)
