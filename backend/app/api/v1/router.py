from fastapi import APIRouter
from .endpoints import auth, questions, quizzes, reports, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(questions.router)
api_router.include_router(quizzes.router)
api_router.include_router(reports.router)
api_router.include_router(users.router)
