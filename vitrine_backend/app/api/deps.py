import threading
from datetime import datetime, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.infrastructure.db.session import SqliteSession
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.domain.models.usuario import Usuario
from app.domain.models.token_blacklist import TokenBlacklist
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


def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> Usuario:
    """Valida o token JWT e retorna o usuário autenticado.

    Verifica:
    - Assinatura e expiração do token (via ``decode_access_token``)
    - Se o ``jti`` do token está na blacklist (revogação individual)
    - Se o ``token_version`` do payload corresponde ao do banco (logout-all)
    """
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        jti = payload.get("jti")
        if not username or not jti:
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido")

    # ── Verifica blacklist (revogação individual) ──────────────────────
    # Sempre verifica — sem bypass por idade de token (M7 removido porque
    # o teste comprova que tokens podem ser revogados imediatamente).
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.jti == jti,
        TokenBlacklist.expires_at > datetime.now(timezone.utc)
    ).first()
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token revogado")

    usuario = UsuarioRepository(db).buscar_por_username(username)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    # ── Verifica token_version (logout-all) ────────────────────────────
    token_version = payload.get("token_version", 0)
    if token_version < usuario.token_version:
        raise HTTPException(status_code=401, detail="Token revogado (logout-all)")

    return usuario


def get_produto_repository(db=Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Retorna o repositório de produtos escopado à empresa do usuário logado.

    ``usuario.empresa_id`` vem sempre da linha fresca do banco (não do JWT
    decodificado direto) — ver get_current_user. Para super_admin
    (empresa_id None) isso levanta erro alto e claro em vez de silenciosamente
    devolver um repositório sem filtro: nenhuma rota de produto hoje é
    acessível por super_admin (não há caso de uso), então chegar aqui com
    empresa_id None é sempre um bug de roteamento, não um caso válido.
    """
    if usuario.empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="Este recurso é por empresa — não disponível para super_admin.",
        )
    return ProdutoRepository(db, empresa_id=usuario.empresa_id)


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
    """Garante que o usuário seja administrador (da própria empresa).

    Intencionalmente NÃO inclui SUPER_ADMIN: rotas de admin operam sobre
    dados de uma empresa (usuario.empresa_id), e super_admin não pertence
    a nenhuma. Área de super_admin usa require_super_admin, separada.
    """
    return require_role(
        usuario,
        [RolesEnum.ADMIN],
        "Acesso restrito a administradores"
    )


def require_super_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    """Garante que o usuário seja super_admin (administra a plataforma,
    não uma empresa específica — usuario.empresa_id é None aqui)."""
    return require_role(
        usuario,
        [RolesEnum.SUPER_ADMIN],
        "Acesso restrito à administração da plataforma"
    )


# ── Injeção de dependência — Adapter de ERP ──────────────────────────

from app.core.interfaces.source import ProductSource, TransactionSource
from app.application.config_service import get as get_config


_ADAPTER_CACHE: dict[str, ProductSource | TransactionSource] = {}
_ADAPTER_LOCK = threading.Lock()

# ── Adapter Registry ──────────────────────────────────────────────────
# Permite registrar múltiplos adapters de ERP sem modificar este arquivo.
# Basta chamar register_adapter() com o nome e as classes do adapter.
# Uso:
#   register_adapter("protheus", ProtheusProductSource, ProtheusTransactionSource)
_ADAPTER_REGISTRY: dict[str, tuple[type[ProductSource], type[TransactionSource]]] = {}


def register_adapter(
    name: str,
    product_source_cls: type[ProductSource],
    transaction_source_cls: type[TransactionSource],
) -> None:
    """Registra um par de classes de adapter para um nome de ERP.

    Args:
        name: Nome do ERP (ex: "alterdata", "protheus").
        product_source_cls: Classe que implementa ``ProductSource``.
        transaction_source_cls: Classe que implementa ``TransactionSource``.
    """
    _ADAPTER_REGISTRY[name] = (product_source_cls, transaction_source_cls)
    import logging
    logging.getLogger(__name__).info("Adapter registrado | erp=%s source=%s tx=%s", name, product_source_cls.__name__, transaction_source_cls.__name__)


# Registro do adapter Alterdata (nativo)
from app.adapters.alterdata.product_source import AlterdataProductSource
from app.adapters.alterdata.transaction_source import AlterdataTransactionSource
register_adapter("alterdata", AlterdataProductSource, AlterdataTransactionSource)


def _get_erp_adapter_name(db, empresa_id: int) -> str:
    """Lê o nome do adapter configurado (ex: 'alterdata') DA EMPRESA."""
    return get_config(db, empresa_id, "erp_adapter", "alterdata")


def get_produto_service(produto_repo=Depends(get_produto_repository)):
    """Retorna o serviço de produtos com o repositório injetado."""
    from app.application.services.produto_service import ProdutoService
    return ProdutoService(produto_repo)


def get_product_source(
    db=Depends(get_db), usuario: Usuario = Depends(get_current_user)
) -> ProductSource:
    """Retorna a fonte de produtos conforme o ERP configurado DA EMPRESA do usuário.

    Consulta o ``_ADAPTER_REGISTRY`` pelo nome do ERP configurado.
    Se o adapter não estiver registrado, levanta ``ValueError``.
    """
    empresa_id = usuario.empresa_id
    erp = _get_erp_adapter_name(db, empresa_id)
    if erp not in _ADAPTER_REGISTRY:
        disponiveis = ", ".join(_ADAPTER_REGISTRY.keys()) or "nenhum"
        raise ValueError(
            f"Adapter não registrado: {erp!r}. "
            f"Adapters disponíveis: {disponiveis}. "
            f"Use register_adapter() para registrar novos adapters."
        )
    with _ADAPTER_LOCK:
        # A chave do cache PRECISA incluir empresa_id: sem isso, a fonte
        # de dados (com a conexão/credenciais do ERP de UMA empresa)
        # seria reusada para servir requests de QUALQUER outra empresa
        # que use o mesmo tipo de adapter (ex: duas empresas "alterdata").
        cache_key = f"product_source:{erp}:{empresa_id}"
        if cache_key not in _ADAPTER_CACHE:
            from app.application.erp_factory import create_product_source
            _ADAPTER_CACHE[cache_key] = create_product_source(db, empresa_id)
        return _ADAPTER_CACHE[cache_key]  # type: ignore[return-value]


def get_transaction_source(
    db=Depends(get_db), usuario: Usuario = Depends(get_current_user)
) -> TransactionSource:
    """Retorna a fonte de transações conforme o ERP configurado DA EMPRESA do usuário.

    Consulta o ``_ADAPTER_REGISTRY`` pelo nome do ERP configurado.
    Se o adapter não estiver registrado, levanta ``ValueError``.
    """
    empresa_id = usuario.empresa_id
    erp = _get_erp_adapter_name(db, empresa_id)
    if erp not in _ADAPTER_REGISTRY:
        disponiveis = ", ".join(_ADAPTER_REGISTRY.keys()) or "nenhum"
        raise ValueError(
            f"Adapter não registrado: {erp!r}. "
            f"Adapters disponíveis: {disponiveis}. "
            f"Use register_adapter() para registrar novos adapters."
        )
    with _ADAPTER_LOCK:
        # Mesma razão do cache_key em get_product_source: precisa incluir
        # empresa_id, senão a conexão do ERP de uma empresa vaza para outra.
        cache_key = f"transaction_source:{erp}:{empresa_id}"
        if cache_key not in _ADAPTER_CACHE:
            from app.application.erp_factory import create_transaction_source
            _ADAPTER_CACHE[cache_key] = create_transaction_source(db, empresa_id)
        return _ADAPTER_CACHE[cache_key]  # type: ignore[return-value]