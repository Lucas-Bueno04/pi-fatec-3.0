from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel
from ..models.question import DifficultyLevel
from ..models.quiz import QuizStatus, HelpType


class QuizStartRequest(BaseModel):
    level: DifficultyLevel


class AnswerSubmit(BaseModel):
    question_id: str
    selected_alternative_id: Optional[str] = None
    association_answers: Optional[Dict[str, str]] = None  # {material_id: target_id}


class HelpRequest(BaseModel):
    question_id: str
    help_type: HelpType


class HelpResponse(BaseModel):
    help_type: HelpType
    eliminated_alternative_ids: Optional[List[str]] = None
    hint_text: Optional[str] = None
    points_deducted: int
    helps_remaining: int


class AnswerResult(BaseModel):
    is_correct: bool
    correct_alternative_id: Optional[str] = None
    explanation: str
    points_earned: int
    current_score: int
    is_last_question: bool


class QuizAnswerResponse(BaseModel):
    question_id: str
    is_correct: bool
    points_earned: int
    helps_used: int = 0


class QuizSessionResponse(BaseModel):
    id: str
    level: DifficultyLevel
    status: QuizStatus
    score: int
    total_possible_score: int
    accuracy_percent: float
    help_count: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    current_question_index: int
    total_questions: int
    question_ids: List[str] = []


class QuizResultResponse(BaseModel):
    session_id: str
    level: DifficultyLevel
    score: int
    total_possible_score: int
    accuracy_percent: float
    correct_count: int
    wrong_count: int
    help_count: int
    level_unlocked: Optional[DifficultyLevel] = None
    answers: List[QuizAnswerResponse]
    started_at: datetime
    finished_at: datetime


class QuizHistoryResponse(BaseModel):
    sessions: List[QuizSessionResponse]
    total: int
