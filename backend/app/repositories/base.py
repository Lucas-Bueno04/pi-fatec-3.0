from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

T = TypeVar("T")


class BaseRepository(Generic[T]):
    collection_name: str
    model_class: Type[T]

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[self.collection_name]

    def _to_object_id(self, id_str: str) -> ObjectId:
        try:
            return ObjectId(id_str)
        except Exception:
            raise ValueError(f"ID inválido: {id_str}")

    async def find_one(self, filter: Dict[str, Any]) -> Optional[T]:
        doc = await self.collection.find_one(filter)
        if doc:
            return self.model_class.from_mongo(doc)
        return None

    async def find_by_id(self, id: str) -> Optional[T]:
        doc = await self.collection.find_one({"_id": self._to_object_id(id)})
        if doc:
            return self.model_class.from_mongo(doc)
        return None

    async def find_many(
        self,
        filter: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List] = None,
    ) -> List[T]:
        cursor = self.collection.find(filter).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = await cursor.to_list(length=limit)
        return [self.model_class.from_mongo(d) for d in docs]

    async def create(self, data: Dict[str, Any]) -> T:
        result = await self.collection.insert_one(data)
        doc = await self.collection.find_one({"_id": result.inserted_id})
        return self.model_class.from_mongo(doc)

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        await self.collection.update_one(
            {"_id": self._to_object_id(id)},
            {"$set": data},
        )
        return await self.find_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": self._to_object_id(id)})
        return result.deleted_count > 0

    async def count(self, filter: Dict[str, Any]) -> int:
        return await self.collection.count_documents(filter)
