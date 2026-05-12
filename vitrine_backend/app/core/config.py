from enum import Enum
from pydantic import model_validator
from pydantic_settings import BaseSettings

class DatabaseType(str, Enum):
    POSTGRES = "postgres"
    SQLITE = "sqlite"

class Settings(BaseSettings):
    postgres_url: str = ""
    sqlite_url: str = ""
    default_db: DatabaseType = DatabaseType.SQLITE

    cache_refresh_interval: int = 3600  # em segundos

    allowed_origins: list[str] = []
    allow_origin_regex: str | None = None

    jwt_secret: str = ""
    access_token_expire_minutes: int = 60 # em minutos

    @model_validator(mode="after")
    def validar_jwt_secret(self):
        if not self.jwt_secret:
            raise ValueError(
                "JWT_SECRET não configurado. "
                "Defina a variável no arquivo .env antes de subir a aplicação."
            )
        if len(self.jwt_secret) < 32:
            raise ValueError(
                "JWT_SECRET muito curto. Use no mínimo 32 caracteres."
            )
        return self

    @model_validator(mode="after")
    def validar_allowed_origins(self):
        if not self.allowed_origins:
            raise ValueError(
                "ALLOWED_ORIGINS não configurado."
                "Defina a variável no arquivo .env antes de subir a aplicação."
            )
        return self

    model_config = {
        "env_file": ".env"
    }

settings = Settings()