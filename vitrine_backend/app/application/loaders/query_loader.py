from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseQueryLoader:
    """Base para carregadores de query SQL."""
    BASE_DIR: Path  # Deve ser definido pela subclasse

    @classmethod
    def load(cls, name: str) -> str:
        logger.debug("Carregando query | nome=%s", name)
        path = cls.BASE_DIR / f"{name}.sql"
        if not path.is_file():
            raise FileNotFoundError(f"Query {name} não encontrada em {path}")
        return path.read_text(encoding="utf-8")
