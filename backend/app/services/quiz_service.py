from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status

from ..core.config import settings
from ..models.quiz import QuizSession, QuizAnswer, QuizStatus, HelpType, HelpUsed
from ..models.question import DifficultyLevel, QuestionType
from ..repositories.quiz_repository import QuizRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.user_repository import UserRepository
from ..schemas.quiz import (
    QuizStartRequest, AnswerSubmit, HelpRequest, HelpResponse,
    AnswerResult, QuizResultResponse, QuizAnswerResponse, QuizSessionResponse,
)


_LEVEL_ORDER = [DifficultyLevel.FACIL, DifficultyLevel.MEDIO, DifficultyLevel.DIFICIL]
_LEVEL_NEXT = {
    DifficultyLevel.FACIL: DifficultyLevel.MEDIO,
    DifficultyLevel.MEDIO: DifficultyLevel.DIFICIL,
    DifficultyLevel.DIFICIL: None,
}
_PROGRESS_UNLOCK_FIELD = {
    DifficultyLevel.MEDIO: "medio_unlocked",
    DifficultyLevel.DIFICIL: "dificil_unlocked",
}
_PROGRESS_BEST_FIELD = {
    DifficultyLevel.FACIL: "facil_best_accuracy",
    DifficultyLevel.MEDIO: "medio_best_accuracy",
    DifficultyLevel.DIFICIL: "dificil_best_accuracy",
}
_POINTS_BY_DIFFICULTY = {
    DifficultyLevel.FACIL: settings.POINTS_EASY,
    DifficultyLevel.MEDIO: settings.POINTS_MEDIUM,
    DifficultyLevel.DIFICIL: settings.POINTS_HARD,
}


class QuizService:
    def __init__(self, db):
        self.quiz_repo = QuizRepository(db)
        self.question_repo = QuestionRepository(db)
        self.user_repo = UserRepository(db)

    async def start_quiz(self, user_id: str, level: DifficultyLevel) -> QuizSessionResponse:
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

        # Check level unlock
        if level == DifficultyLevel.MEDIO and not user.progress.medio_unlocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nível Médio ainda não desbloqueado.")
        if level == DifficultyLevel.DIFICIL and not user.progress.dificil_unlocked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nível Difícil ainda não desbloqueado.")

        # Abandon any active session
        active = await self.quiz_repo.find_active_session(user_id)
        if active:
            await self.quiz_repo.update_session(active.id, {
                "status": QuizStatus.ABANDONED.value,
                "finished_at": datetime.utcnow(),
            })

        questions = await self.question_repo.find_for_quiz(
            settings.QUIZ_EASY_COUNT,
            settings.QUIZ_MEDIUM_COUNT,
            settings.QUIZ_HARD_COUNT,
        )

        total_possible = sum(
            _POINTS_BY_DIFFICULTY[q.difficulty] for q in questions
        )

        session = QuizSession(
            user_id=user_id,
            level=level,
            question_ids=[q.id for q in questions],
            total_possible_score=total_possible,
        )
        saved = await self.quiz_repo.create_session(session)

        return QuizSessionResponse(
            id=saved.id,
            level=saved.level,
            status=saved.status,
            score=saved.score,
            total_possible_score=saved.total_possible_score,
            accuracy_percent=0.0,
            help_count=0,
            started_at=saved.started_at,
            finished_at=None,
            current_question_index=0,
            total_questions=len(questions),
            question_ids=saved.question_ids,
        )

    async def submit_answer(self, session_id: str, user_id: str, data: AnswerSubmit) -> AnswerResult:
        session = await self._get_active_session(session_id, user_id)
        q_id = data.question_id

        if q_id not in session.question_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Questão não pertence a esta sessão.")

        already_answered = [a for a in session.answers if a.question_id == q_id]
        if already_answered:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Questão já respondida.")

        question = await self.question_repo.find_by_id(q_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada.")

        is_correct = False
        points = 0

        if question.type == QuestionType.MULTIPLA_ESCOLHA:
            is_correct = data.selected_alternative_id == question.correct_alternative_id
        elif question.type in (QuestionType.ASSOCIACAO_FUNCAO, QuestionType.ASSOCIACAO_SISTEMA):
            if data.association_answers:
                correct_map = {p.material_id: p.target_id for p in question.association_pairs}
                is_correct = data.association_answers == correct_map

        if is_correct:
            points = _POINTS_BY_DIFFICULTY[question.difficulty]

        answer = QuizAnswer(
            question_id=q_id,
            selected_alternative_id=data.selected_alternative_id,
            association_answers=data.association_answers,
            is_correct=is_correct,
            points_earned=points,
        )

        updated_answers = session.answers + [answer]
        new_score = session.score + points
        new_index = session.current_question_index + 1
        is_last = new_index >= len(session.question_ids)

        await self.quiz_repo.update_session(session_id, {
            "answers": [a.model_dump() for a in updated_answers],
            "score": new_score,
            "current_question_index": new_index,
        })

        return AnswerResult(
            is_correct=is_correct,
            correct_alternative_id=question.correct_alternative_id,
            explanation=question.explanation,
            points_earned=points,
            current_score=new_score,
            is_last_question=is_last,
        )

    async def use_help(self, session_id: str, user_id: str, data: HelpRequest) -> HelpResponse:
        session = await self._get_active_session(session_id, user_id)

        if session.help_count >= settings.MAX_HELPS_PER_QUIZ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de {settings.MAX_HELPS_PER_QUIZ} ajudas por quiz atingido.",
            )

        question = await self.question_repo.find_by_id(data.question_id)
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada.")

        cost = settings.HELP_ELIMINATE_COST if data.help_type == HelpType.ELIMINATE_TWO else settings.HELP_HINT_COST
        new_score = max(0, session.score - cost)

        eliminated = None
        hint = None

        if data.help_type == HelpType.ELIMINATE_TWO:
            wrong_alts = [a.id for a in question.alternatives if not a.is_correct]
            import random
            eliminated = random.sample(wrong_alts, min(2, len(wrong_alts)))
        else:
            hint = question.explanation[:120] + "..." if len(question.explanation) > 120 else question.explanation

        help_used = HelpUsed(
            help_type=data.help_type,
            question_id=data.question_id,
            points_deducted=cost,
        )
        updated_answers = session.answers.copy()
        # Attach help to the current question answer if already answered, else track separately
        await self.quiz_repo.update_session(session_id, {
            "score": new_score,
            "help_count": session.help_count + 1,
        })

        return HelpResponse(
            help_type=data.help_type,
            eliminated_alternative_ids=eliminated,
            hint_text=hint,
            points_deducted=cost,
            helps_remaining=settings.MAX_HELPS_PER_QUIZ - (session.help_count + 1),
        )

    async def finish_quiz(self, session_id: str, user_id: str) -> QuizResultResponse:
        session = await self._get_active_session(session_id, user_id)

        total_q = len(session.question_ids)
        correct = sum(1 for a in session.answers if a.is_correct)
        accuracy = (correct / total_q * 100) if total_q > 0 else 0.0
        now = datetime.utcnow()

        await self.quiz_repo.update_session(session_id, {
            "status": QuizStatus.COMPLETED.value,
            "finished_at": now,
            "accuracy_percent": accuracy,
        })

        # Check level unlock
        unlocked_level = None
        user = await self.user_repo.find_by_id(user_id)
        if user and accuracy >= settings.QUIZ_UNLOCK_MIN_ACCURACY:
            next_level = _LEVEL_NEXT.get(session.level)
            if next_level and not getattr(user.progress, _PROGRESS_UNLOCK_FIELD.get(next_level, ""), True):
                unlocked_level = next_level
                update_data = {_PROGRESS_UNLOCK_FIELD[next_level]: True}
                best_field = _PROGRESS_BEST_FIELD.get(session.level)
                if best_field:
                    current_best = getattr(user.progress, best_field, 0.0)
                    update_data[best_field] = max(current_best, accuracy)
                new_progress = user.progress.model_copy(update=update_data)
                await self.user_repo.update_progress(user_id, new_progress)
        elif user:
            best_field = _PROGRESS_BEST_FIELD.get(session.level)
            if best_field:
                current_best = getattr(user.progress, best_field, 0.0)
                if accuracy > current_best:
                    new_progress = user.progress.model_copy(update={best_field: accuracy})
                    await self.user_repo.update_progress(user_id, new_progress)

        return QuizResultResponse(
            session_id=session_id,
            level=session.level,
            score=session.score,
            total_possible_score=session.total_possible_score,
            accuracy_percent=accuracy,
            correct_count=correct,
            wrong_count=total_q - correct,
            help_count=session.help_count,
            level_unlocked=unlocked_level,
            answers=[
                QuizAnswerResponse(
                    question_id=a.question_id,
                    is_correct=a.is_correct,
                    points_earned=a.points_earned,
                    helps_used=len(a.helps_used),
                )
                for a in session.answers
            ],
            started_at=session.started_at,
            finished_at=now,
        )

    async def get_history(self, user_id: str) -> list:
        sessions = await self.quiz_repo.find_by_user(user_id)
        return [
            QuizSessionResponse(
                id=s.id,
                level=s.level,
                status=s.status,
                score=s.score,
                total_possible_score=s.total_possible_score,
                accuracy_percent=s.accuracy_percent,
                help_count=s.help_count,
                started_at=s.started_at,
                finished_at=s.finished_at,
                current_question_index=s.current_question_index,
                total_questions=len(s.question_ids),
            )
            for s in sessions
        ]

    async def _get_active_session(self, session_id: str, user_id: str) -> QuizSession:
        session = await self.quiz_repo.find_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada.")
        if session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
        if session.status != QuizStatus.IN_PROGRESS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sessão não está em andamento.")
        return session
