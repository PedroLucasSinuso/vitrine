from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.infrastructure.db.session import SqliteSession
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.domain.models.usuario import Usuario
from app.domain.enums import RolesEnum
from app.application.utils.jwt_handler import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db():
    """Retorna uma sessão do banco SQLite."""
    session = SqliteSession()
    try:
        yield session
    finally:
        session.close()


def get_produto_repository(db=Depends(get_db)):
    """Retorna o repositório de produtos."""
    return ProdutoRepository(db)


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> Usuario:
    """Valida o token JWT e retorna o usuário autenticado."""
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not username:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = UsuarioRepository(db).buscar_por_username(username)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return usuario


def require_role(usuario: Usuario, allowed_roles: list[RolesEnum], detail: str) -> Usuario:
    """Verifica se o usuário tem um dos roles permitidos, senão levanta 403."""
    if usuario.role not in [r.value for r in allowed_roles]:
        raise HTTPException(status_code=403, detail=detail)
    return usuario


def require_supervisor(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Garante que o usuário seja supervisor ou admin."""
    return require_role(
        usuario,
        [RolesEnum.SUPERVISOR, RolesEnum.ADMIN],
        "Acesso restrito a supervisores"
    )


def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Garante que o usuário seja administrador."""
    return require_role(
        usuario,
        [RolesEnum.ADMIN],
        "Acesso restrito a administradores"
    )


# ── Injeção de dependência — Adapter de ERP ──────────────────────────

from app.core.interfaces.source import ProductSource, TransactionSource
from app.application.config_service import get as get_config


_ADAPTER_CACHE: dict[str, ProductSource | TransactionSource] = {}


def _get_erp_adapter_name(db) -> str:
    """Lê o nome do adapter configurado (ex: 'alterdata')."""
    return get_config(db, "erp_adapter", "alterdata")


def get_product_source(db=Depends(get_db)) -> ProductSource:
    """Retorna a fonte de produtos conforme o ERP configurado."""
    erp = _get_erp_adapter_name(db)
    if erp != "alterdata":
        raise ValueError(f"Adapter não implementado: {erp}")
    if "product_source" not in _ADAPTER_CACHE:
        from app.adapters.alterdata.product_source import AlterdataProductSource
        from app.adapters.alterdata.db import get_alterdata_engine
        _ADAPTER_CACHE["product_source"] = AlterdataProductSource(get_alterdata_engine(db))
    return _ADAPTER_CACHE["product_source"]


def get_transaction_source(db=Depends(get_db)) -> TransactionSource:
    """Retorna a fonte de transações conforme o ERP configurado."""
    erp = _get_erp_adapter_name(db)
    if erp != "alterdata":
        raise ValueError(f"Adapter não implementado: {erp}")
    if "transaction_source" not in _ADAPTER_CACHE:
        from app.adapters.alterdata.transaction_source import AlterdataTransactionSource
        from app.adapters.alterdata.db import get_alterdata_engine
        _ADAPTER_CACHE["transaction_source"] = AlterdataTransactionSource(get_alterdata_engine(db))
    return _ADAPTER_CACHE["transaction_source"]