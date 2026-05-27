from app.infrastructure.db.database import Base

from app.domain.models.produto import Produto, ProdutoCodigo
from app.domain.models.cache_status import CacheStatus
from app.domain.models.sync_job import SyncJob
from app.domain.models.token_blacklist import TokenBlacklist
from app.domain.models.tentativa_login import TentativaLogin
from app.domain.models.grupo_familia import GrupoFamilia
from app.domain.models.intelligence_cache import IntelligenceCache
from app.domain.models.intelligence_job import IntelligenceJob
from app.domain.models.intelligence_usage import IntelligenceUsage
from app.domain.models.intelligence_dismissed import InsightsDismissed

__all__ = [
    "Base", "Produto", "ProdutoCodigo", "CacheStatus", "SyncJob",
    "TokenBlacklist", "TentativaLogin", "GrupoFamilia",
    "IntelligenceCache", "IntelligenceJob", "IntelligenceUsage", "InsightsDismissed",
]