from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from ....core.database import get_database
from ....models.user import UserRole
from ....models.question import DifficultyLevel
from ....schemas.report import StudentReport, ClassReport, TeacherDashboard, ReportFilter
from ....services.report_service import ReportService
from ....security.jwt import get_current_active_user, require_role

router = APIRouter(prefix="/reports", tags=["Relatórios"])

_teacher_or_admin = require_role(UserRole.PROFESSOR, UserRole.ADMINISTRADOR)


@router.get("/my-report", response_model=StudentReport)
async def my_report(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    level: Optional[DifficultyLevel] = Query(None),
    current_user=Depends(get_current_active_user),
    db=Depends(get_database),
):
    """Relatório de desempenho do aluno autenticado."""
    service = ReportService(db)
    return await service.get_student_report(
        current_user.id,
        ReportFilter(date_from=date_from, date_to=date_to, level=level),
    )


@router.get("/student/{student_id}", response_model=StudentReport)
async def student_report(
    student_id: str,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    level: Optional[DifficultyLevel] = Query(None),
    _=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    """Relatório de desempenho de um aluno específico."""
    service = ReportService(db)
    return await service.get_student_report(
        student_id,
        ReportFilter(date_from=date_from, date_to=date_to, level=level),
    )


@router.get("/class/{class_name}", response_model=ClassReport)
async def class_report(
    class_name: str,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    _=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    """Relatório consolidado da turma."""
    service = ReportService(db)
    return await service.get_class_report(class_name, ReportFilter(date_from=date_from, date_to=date_to))


@router.get("/dashboard", response_model=TeacherDashboard)
async def teacher_dashboard(
    current_user=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    """Dashboard pedagógico do professor."""
    service = ReportService(db)
    return await service.get_teacher_dashboard(current_user.id)
