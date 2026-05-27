from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "LabQuiz ETEC"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # MongoDB — individual params to avoid URL encoding issues
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_USERNAME: str = "admin"
    MONGO_PASSWORD: str = "admin123"
    DB_NAME: str = "labquiz_etec"
    GRIDFS_BUCKET: str = "images"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str = "changeme-super-secret-key-minimum-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS — plain string; parsed via property to avoid pydantic-settings JSON coercion
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost"

    # Quiz rules
    QUIZ_EASY_COUNT: int = 4
    QUIZ_MEDIUM_COUNT: int = 3
    QUIZ_HARD_COUNT: int = 3
    QUIZ_UNLOCK_MIN_ACCURACY: float = 70.0

    # Points
    POINTS_EASY: int = 10
    POINTS_MEDIUM: int = 20
    POINTS_HARD: int = 30
    HELP_ELIMINATE_COST: int = 5
    HELP_HINT_COST: int = 3
    MAX_HELPS_PER_QUIZ: int = 2

    @property
    def cors_origins_list(self) -> List[str]:
        v = self.CORS_ORIGINS.strip()
        if v.startswith("["):
            return json.loads(v)
        return [o.strip() for o in v.split(",") if o.strip()]


settings = Settings()
