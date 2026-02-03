from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """Загрузка переменных окружения"""

    model_config = SettingsConfigDict(
        env_file=str(env_path), case_sensitive=True, extra="ignore"
    )

    # Режим отладки приложения (ВАЖНО для безопасности!)
    # Если True - пользователи ВИДЯТ полные traceback ошибок в HTTP-ответах (DevTools, на экране)
    # Если False - пользователи видят только request_id, traceback остается ТОЛЬКО в логах на сервере
    # Также контролирует: формат логов (цветной текст vs JSON)
    # Development: True, Production: False (ОБЯЗАТЕЛЬНО!)
    DEBUG: bool = False

    # Уровень детализации логирования на сервере (независим от DEBUG)
    # Возможные значения: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    LOG_LEVEL: str = "INFO"

    # Вывод SQL-запросов SQLAlchemy в консоль (независим от DEBUG)
    # Если True - все SQL-запросы выводятся в консоль
    DB_ECHO: bool = False

    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = ""
    DB_PASS: str = ""
    DB_NAME: str = "auth_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # JWT settings
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # Frontend URL for redirects after OAuth
    FRONTEND_URL: str = "http://localhost:3000"

    # Cookie settings
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"

    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Session settings (for OAuth state)
    SESSION_SECRET_KEY: str = ""


settings = Settings()
