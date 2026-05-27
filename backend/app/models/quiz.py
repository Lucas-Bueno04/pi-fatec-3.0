from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .question import DifficultyLevel


class HelpType(str, Enum):
    ELIMINATE_TWO = "ELIMINATE_TWO"
    TEXT_HINT = "TEXT_HINT"


class QuizStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class HelpUsed(BaseModel):
    help_type: HelpType
    question_id: str
    points_deducted: int


class QuizAnswer(BaseModel):
    question_id: str
    selected_alternative_id: Optional[str] = None
    association_answers: Optional[Dict[str, str]] = None  # for association questions
    is_correct: bool = False
    time_taken_seconds: float = 0.0
    points_earned: int = 0
    helps_used: List[HelpUsed] = Field(default_factory=list)


class QuizSession(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    level: DifficultyLevel
    question_ids: List[str] = Field(default_factory=list)
    current_question_index: int = 0
    answers: List[QuizAnswer] = Field(default_factory=list)
    score: int = 0
    total_possible_score: int = 0
    accuracy_percent: float = 0.0
    help_count: int = 0
    status: QuizStatus = QuizStatus.IN_PROGRESS
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> Dict[str, Any]:
        data = self.model_dump(exclude={"id"}, by_alias=False)
        data["answers"] = [a.model_dump() for a in self.answers]
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "QuizSession":
        if data and "_id" in data:
            data["_id"] = str(data["_id"])
        return cls(**data)
