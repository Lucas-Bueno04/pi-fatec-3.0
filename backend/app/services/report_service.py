from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, status

from ..models.quiz import QuizStatus
from ..models.question import DifficultyLevel
from ..repositories.quiz_repository import QuizRepository
from ..repositories.user_repository import UserRepository
from ..schemas.report import (
    StudentReport, ClassReport, TeacherDashboard,
    StudentSummary, SessionSummary, ReportFilter,
)


class ReportService:
    def __init__(self, db):
        self.quiz_repo = QuizRepository(db)
        self.user_repo = UserRepository(db)

    async def get_student_report(self, student_id: str, filters: ReportFilter) -> StudentReport:
        user = await self.user_repo.find_by_id(student_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

        sessions = await self.quiz_repo.find_by_user(student_id, limit=200)
        completed = [s for s in sessions if s.status == QuizStatus.COMPLETED]

        if filters.date_from:
            completed = [s for s in completed if s.started_at >= filters.date_from]
        if filters.date_to:
            completed = [s for s in completed if s.started_at <= filters.date_to]
        if filters.level:
            completed = [s for s in completed if s.level == filters.level]

        avg_acc = (sum(s.accuracy_percent for s in completed) / len(completed)) if completed else 0.0
        best_acc = max((s.accuracy_percent for s in completed), default=0.0)
        total_score = sum(s.score for s in completed)

        level_counts = {DifficultyLevel.FACIL: 0, DifficultyLevel.MEDIO: 0, DifficultyLevel.DIFICIL: 0}
        for s in completed:
            level_counts[s.level] = level_counts.get(s.level, 0) + 1

        levels_reached = [s.level for s in completed]
        level_order = [DifficultyLevel.FACIL, DifficultyLevel.MEDIO, DifficultyLevel.DIFICIL]
        max_level = None
        for lv in reversed(level_order):
            if lv in levels_reached:
                max_level = lv
                break

        recent = sorted(completed, key=lambda s: s.started_at, reverse=True)[:10]

        return StudentReport(
            user_id=user.id,
            name=user.name,
            email=user.email,
            class_name=user.class_name,
            total_games=len(completed),
            avg_accuracy=round(avg_acc, 2),
            best_accuracy=round(best_acc, 2),
            max_level_reached=max_level,
            total_score=total_score,
            facil_games=level_counts[DifficultyLevel.FACIL],
            medio_games=level_counts[DifficultyLevel.MEDIO],
            dificil_games=level_counts[DifficultyLevel.DIFICIL],
            recent_sessions=[
                SessionSummary(
                    session_id=s.id,
                    level=s.level,
                    score=s.score,
                    accuracy_percent=s.accuracy_percent,
                    help_count=s.help_count,
                    played_at=s.started_at,
                )
                for s in recent
            ],
        )

    async def get_class_report(self, class_name: str, filters: ReportFilter) -> ClassReport:
        students = await self.user_repo.list_by_class(class_name)
        summaries = []
        total_acc = 0.0
        count_with_games = 0

        for student in students:
            sessions = await self.quiz_repo.find_by_user(student.id, limit=100)
            completed = [s for s in sessions if s.status == QuizStatus.COMPLETED]
            avg = (sum(s.accuracy_percent for s in completed) / len(completed)) if completed else 0.0
            last = max((s.started_at for s in completed), default=None)
            levels_reached = [s.level for s in completed]
            level_order = [DifficultyLevel.FACIL, DifficultyLevel.MEDIO, DifficultyLevel.DIFICIL]
            max_level = None
            for lv in reversed(level_order):
                if lv in levels_reached:
                    max_level = lv
                    break

            if completed:
                total_acc += avg
                count_with_games += 1

            summaries.append(StudentSummary(
                user_id=student.id,
                name=student.name,
                total_games=len(completed),
                avg_accuracy=round(avg, 2),
                max_level_reached=max_level,
                last_activity=last,
            ))

        class_avg = (total_acc / count_with_games) if count_with_games else 0.0

        return ClassReport(
            class_name=class_name,
            total_students=len(students),
            avg_accuracy=round(class_avg, 2),
            students=summaries,
        )

    async def get_teacher_dashboard(self, teacher_id: str) -> TeacherDashboard:
        teacher = await self.user_repo.find_by_id(teacher_id)
        if not teacher:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado.")

        all_students = await self.user_repo.find_many(
            {"role": "ALUNO", "is_active": True}, limit=500
        )

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = datetime.utcnow() - timedelta(days=7)

        games_today = 0
        week_accuracies = []
        summaries = []

        for student in all_students:
            sessions = await self.quiz_repo.find_by_user(student.id, limit=50)
            completed = [s for s in sessions if s.status == QuizStatus.COMPLETED]
            games_today += sum(1 for s in completed if s.started_at >= today)
            week_accuracies.extend(s.accuracy_percent for s in completed if s.started_at >= week_ago)
            avg = (sum(s.accuracy_percent for s in completed) / len(completed)) if completed else 0.0
            summaries.append(StudentSummary(
                user_id=student.id,
                name=student.name,
                total_games=len(completed),
                avg_accuracy=round(avg, 2),
                last_activity=max((s.started_at for s in completed), default=None),
            ))

        week_avg = (sum(week_accuracies) / len(week_accuracies)) if week_accuracies else 0.0
        top = sorted(summaries, key=lambda s: s.avg_accuracy, reverse=True)[:5]
        struggling = [s for s in summaries if s.avg_accuracy < 50.0 and s.total_games > 0][:5]

        return TeacherDashboard(
            total_students=len(all_students),
            total_games_today=games_today,
            avg_accuracy_this_week=round(week_avg, 2),
            top_students=top,
            struggling_students=struggling,
        )
