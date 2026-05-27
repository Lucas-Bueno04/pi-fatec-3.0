from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    MULTIPLA_ESCOLHA = "MULTIPLA_ESCOLHA"
    ASSOCIACAO_FUNCAO = "ASSOCIACAO_FUNCAO"
    ASSOCIACAO_SISTEMA = "ASSOCIACAO_SISTEMA"


class DifficultyLevel(str, Enum):
    FACIL = "FACIL"
    MEDIO = "MEDIO"
    DIFICIL = "DIFICIL"


class Alternative(BaseModel):
    id: str
    text: str
    image_id: Optional[str] = None  # GridFS reference
    alt_text: Optional[str] = None  # accessibility
    is_correct: bool = False


class AssociationPair(BaseModel):
    material_id: str
    material_name: str
    material_image_id: Optional[str] = None
    target_id: str
    target_text: str


class Question(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    type: QuestionType
    difficulty: DifficultyLevel
    text: str
    image_id: Optional[str] = None
    image_alt_text: Optional[str] = None
    alternatives: List[Alternative] = Field(default_factory=list)
    correct_alternative_id: Optional[str] = None
    association_pairs: List[AssociationPair] = Field(default_factory=list)
    explanation: str = ""
    material_name: Optional[str] = None
    function_text: Optional[str] = None
    system_name: Optional[str] = None
    created_by: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        data = self.model_dump(exclude={"id"}, by_alias=False)
        data["alternatives"] = [a.model_dump() for a in self.alternatives]
        data["association_pairs"] = [p.model_dump() for p in self.association_pairs]
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "Question":
        if data and "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
