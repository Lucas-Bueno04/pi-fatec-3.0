from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from ..models.question import DifficultyLevel


class ReportFilter(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    level: Optional[DifficultyLevel] = None


class SessionSummary(BaseModel):
    session_id: str
    level: DifficultyLevel
    score: int
    accuracy_percent: float
    help_count: int
    played_at: datetime


class StudentReport(BaseModel):
    user_id: str
    name: str
    email: str
    class_name: Optional[str] = None
    total_games: int
    avg_accuracy: float
    best_accuracy: float
    max_level_reached: Optional[DifficultyLevel] = None
    total_score: int
    facil_games: int
    medio_games: int
    dificil_games: int
    recent_sessions: List[SessionSummary]


class StudentSummary(BaseModel):
    user_id: str
    name: str
    total_games: int
    avg_accuracy: float
    max_level_reached: Optional[DifficultyLevel] = None
    last_activity: Optional[datetime] = None


class ClassReport(BaseModel):
    class_name: str
    total_students: int
    avg_accuracy: float
    students: List[StudentSummary]


class TeacherDashboard(BaseModel):
    total_students: int
    total_games_today: int
    avg_accuracy_this_week: float
    top_students: List[StudentSummary]
    struggling_students: List[StudentSummary]  # accuracy < 50%
