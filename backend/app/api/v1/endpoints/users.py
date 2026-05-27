from typing import List
from fastapi import APIRouter, Depends, status

from ....core.database import get_database
from ....models.user import UserRole
from ....schemas.user import UserResponse, UserUpdate
from ....security.jwt import require_role

router = APIRouter(prefix="/users", tags=["Usuários"])

_admin = require_role(UserRole.ADMINISTRADOR)
_teacher_or_admin = require_role(UserRole.PROFESSOR, UserRole.ADMINISTRADOR)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _=Depends(_admin),
    db=Depends(get_database),
):
    """Lista todos os usuários (apenas administradores)."""
    from ....repositories.user_repository import UserRepository
    repo = UserRepository(db)
    users = await repo.find_many({}, skip=skip, limit=limit)
    return [
        UserResponse(
            id=u.id, name=u.name, email=u.email, role=u.role,
            class_name=u.class_name, is_active=u.is_active,
            progress=u.progress, created_at=u.created_at,
        )
        for u in users
    ]


@router.get("/class/{class_name}/students", response_model=List[UserResponse])
async def list_students_by_class(
    class_name: str,
    _=Depends(_teacher_or_admin),
    db=Depends(get_database),
):
    """Lista alunos de uma turma."""
    from ....repositories.user_repository import UserRepository
    repo = UserRepository(db)
    students = await repo.list_by_class(class_name)
    return [
        UserResponse(
            id=u.id, name=u.name, email=u.email, role=u.role,
            class_name=u.class_name, is_active=u.is_active,
            progress=u.progress, created_at=u.created_at,
        )
        for u in students
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    _=Depends(_admin),
    db=Depends(get_database),
):
    from ....repositories.user_repository import UserRepository
    from fastapi import HTTPException
    repo = UserRepository(db)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return UserResponse(
        id=user.id, name=user.name, email=user.email, role=user.role,
        class_name=user.class_name, is_active=user.is_active,
        progress=user.progress, created_at=user.created_at,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    _=Depends(_admin),
    db=Depends(get_database),
):
    from ....repositories.user_repository import UserRepository
    from fastapi import HTTPException
    repo = UserRepository(db)
    updated = await repo.update_user(user_id, data.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return UserResponse(
        id=updated.id, name=updated.name, email=updated.email, role=updated.role,
        class_name=updated.class_name, is_active=updated.is_active,
        progress=updated.progress, created_at=updated.created_at,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    _=Depends(_admin),
    db=Depends(get_database),
):
    from ....repositories.user_repository import UserRepository
    repo = UserRepository(db)
    await repo.update_user(user_id, {"is_active": False})
