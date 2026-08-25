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


_ADAPTER_CACHE: dict[str, ProductSource | TransactionSource] = {}
_ADAPTER_LOCK = threading.Lock()


def _nome_adapter(db, empresa_id: int) -> str:
    """Nome do ERP configurado para a empresa (delegado ao erp_factory)."""
    from app.application.erp_factory import nome_adapter

    return nome_adapter(db, empresa_id)


def limpar_cache_adapters(empresa_id: int | None = None) -> None:
    """Descarta fontes de dados cacheadas.

    O cache não tem TTL (vive pelo processo), então trocar o ``erp_adapter``
    de uma empresa — ou resetar o tenant de demo — não teria efeito sem isto.
    Sem ``empresa_id``, limpa tudo.
    """
    with _ADAPTER_LOCK:
        if empresa_id is None:
            _ADAPTER_CACHE.clear()
            return
        sufixo = f":{empresa_id}"
        for chave in [k for k in _ADAPTER_CACHE if k.endswith(sufixo)]:
            del _ADAPTER_CACHE[chave]


def get_produto_service(produto_repo=Depends(get_produto_repository)):
    """Retorna o serviço de produtos com o repositório injetado."""
    from app.application.services.produto_service import ProdutoService
    return ProdutoService(produto_repo)


def get_product_source(
    db=Depends(get_db), usuario: Usuario = Depends(get_current_user)
) -> ProductSource:
    """Retorna a fonte de produtos do ERP DA EMPRESA do usuário.

    O adapter concreto vem da configuração ``erp_adapter`` da empresa,
    resolvida pelo registry — ver ``app/application/adapter_registry.py``.
    """
    empresa_id = usuario.empresa_id
    if empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="Este recurso é por empresa — não disponível para super_admin.",
        )
    erp = _nome_adapter(db, empresa_id)
    with _ADAPTER_LOCK:
        # A chave PRECISA incluir empresa_id: sem isso, a fonte de dados
        # (com a conexão/credenciais do ERP de UMA empresa) seria reusada
        # para servir requests de QUALQUER outra que use o mesmo adapter.
        cache_key = f"product_source:{erp}:{empresa_id}"
        if cache_key not in _ADAPTER_CACHE:
            from app.application.adapter_registry import AdapterNaoRegistradoError
            from app.application.erp_factory import create_product_source

            try:
                _ADAPTER_CACHE[cache_key] = create_product_source(db, empresa_id)
            except AdapterNaoRegistradoError as e:
                # Configuração inválida do tenant, não bug do servidor.
                raise HTTPException(status_code=400, detail=str(e)) from e
        return _ADAPTER_CACHE[cache_key]  # type: ignore[return-value]


def get_transaction_source(
    db=Depends(get_db), usuario: Usuario = Depends(get_current_user)
) -> TransactionSource:
    """Retorna a fonte de transações do ERP DA EMPRESA do usuário.

    O adapter concreto vem da configuração ``erp_adapter`` da empresa,
    resolvida pelo registry — ver ``app/application/adapter_registry.py``.
    """
    empresa_id = usuario.empresa_id
    if empresa_id is None:
        raise HTTPException(
            status_code=403,
            detail="Este recurso é por empresa — não disponível para super_admin.",
        )
    erp = _nome_adapter(db, empresa_id)
    with _ADAPTER_LOCK:
        # A chave PRECISA incluir empresa_id: sem isso, a fonte de dados
        # (com a conexão/credenciais do ERP de UMA empresa) seria reusada
        # para servir requests de QUALQUER outra que use o mesmo adapter.
        cache_key = f"transaction_source:{erp}:{empresa_id}"
        if cache_key not in _ADAPTER_CACHE:
            from app.application.adapter_registry import AdapterNaoRegistradoError
            from app.application.erp_factory import create_transaction_source

            try:
                _ADAPTER_CACHE[cache_key] = create_transaction_source(db, empresa_id)
            except AdapterNaoRegistradoError as e:
                # Configuração inválida do tenant, não bug do servidor.
                raise HTTPException(status_code=400, detail=str(e)) from e
        return _ADAPTER_CACHE[cache_key]  # type: ignore[return-value]

