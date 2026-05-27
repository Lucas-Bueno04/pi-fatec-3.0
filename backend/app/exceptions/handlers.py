from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class QuizNotFoundException(AppException):
    def __init__(self):
        super().__init__(status.HTTP_404_NOT_FOUND, "Sessão de quiz não encontrada.")


class LevelLockedError(AppException):
    def __init__(self, level: str):
        super().__init__(status.HTTP_403_FORBIDDEN, f"Nível '{level}' ainda não desbloqueado.")


class HelpLimitExceededError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "Limite de ajudas atingido para este quiz.")


class InvalidAnswerError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "Resposta inválida.")


class LGPDConsentRequiredError(AppException):
    def __init__(self):
        super().__init__(status.HTTP_400_BAD_REQUEST, "Consentimento LGPD é obrigatório.")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            loc = " → ".join(str(l) for l in error["loc"] if l != "body")
            errors.append(f"{loc}: {error['msg']}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Erro de validação.", "errors": errors},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
