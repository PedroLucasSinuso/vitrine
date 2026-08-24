from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.limiter import limiter
import logging

from app.api.deps import get_db, require_admin, get_current_user, oauth2_scheme
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.application.services.auth_service import AuthService
from app.application.utils.jwt_handler import decode_access_token
from app.schemas.auth_schema import TokenResponse, RefreshRequest, MessageResponse
from app.schemas.usuario_schema import UsuarioCreate, UsuarioPatch, UsuarioResponse
from app.domain.models.usuario import Usuario
from app.domain.models.token_blacklist import TokenBlacklist
from app.domain.models.tentativa_login import TentativaLogin

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)

LOGIN_LOCKOUT_MINUTES = 15
LOGIN_MAX_ATTEMPTS = 5


def _contar_tentativas_falhas(db: Session, username: str) -> int:
    """Conta tentativas falhas de login para o username nos últimos N minutos."""
    limite = datetime.now(timezone.utc) - timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
    stmt = select(func.count()).where(
        TentativaLogin.username == username,
        TentativaLogin.sucesso == False,
        TentativaLogin.attempted_at >= limite,
    )
    return db.execute(stmt).scalar() or 0


def _limpar_tentativas_falhas(db: Session, username: str) -> None:
    """Remove tentativas falhas do username após login bem sucedido."""
    stmt = select(TentativaLogin).where(
        TentativaLogin.username == username,
        TentativaLogin.sucesso == False,
    )
    for tentativa in db.execute(stmt).scalars().all():
        db.delete(tentativa)
    db.flush()


@router.post("/token", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, dados: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # ── Lockout check ──────────────────────────────────────────────
    tentativas = _contar_tentativas_falhas(db, dados.username)
    if tentativas >= LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Tente novamente em 15 minutos.",
        )

    # ── Tentativa de autenticação ──────────────────────────────────
    service = AuthService(UsuarioRepository(db))
    try:
        access_token, refresh_token = service.autenticar(dados.username, dados.password)
    except ValueError:
        # Registra tentativa falha
        db.add(TentativaLogin(
            username=dados.username,
            ip_address=request.client.host if request.client else None,
            sucesso=False,
        ))
        db.commit()
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # Login bem sucedido — limpa falhas anteriores
    _limpar_tentativas_falhas(db, dados.username)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
def refresh(request: Request, body: RefreshRequest, db: Session = Depends(get_db)):
    """Troca um refresh token válido por um NOVO par (access + refresh).

    - Verifica assinatura, expiração e type == 'refresh'
    - Verifica token_version do usuário (logout-all)
    - Emite novos tokens com rotação completa
    """
    service = AuthService(UsuarioRepository(db))
    try:
        access_token, refresh_token = service.refresh(body.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UsuarioResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, response: Response, dados: UsuarioCreate, db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
    service = AuthService(UsuarioRepository(db))
    try:
        usuario = service.registrar(dados, empresa_id=_admin.empresa_id)
        db.commit()
        return usuario
    except ValueError as e:
        logger.warning("Erro ao registrar usuario | Erro: %s", e)
        raise HTTPException(status_code=409, detail="Usuario ja existe ou dados invalidos")


@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
    return AuthService(UsuarioRepository(db)).listar(empresa_id=_admin.empresa_id)


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioPatch,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    service = AuthService(UsuarioRepository(db))
    try:
        usuario = service.atualizar(usuario_id, dados, empresa_id=_admin.empresa_id)
        db.commit()
        return usuario
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/usuarios/{usuario_id}", status_code=204)
def excluir_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    service = AuthService(UsuarioRepository(db))
    try:
        service.excluir(usuario_id, admin.id, empresa_id=admin.empresa_id)
        db.commit()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
@limiter.limit("10/minute")
def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Revoga o token JWT atual individualmente."""
    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido")

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        raise HTTPException(status_code=400, detail="Token inválido: sem jti ou exp")

    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

    entry = TokenBlacklist(
        jti=jti,
        user_id=current_user.id,
        expires_at=expires_at,
        revoked_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    return MessageResponse(message="Token revogado com sucesso")


@router.post("/logout-all", response_model=MessageResponse)
@limiter.limit("5/minute")
def logout_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Revoga todos os tokens do usuário incrementando o ``token_version``.

    Todos os tokens JWT emitidos antes desta chamada tornam-se inválidos,
    pois o ``token_version`` armazenado no payload será menor que o valor
    atual no banco.
    """
    current_user.token_version += 1
    db.commit()
    return MessageResponse(message="Todos os tokens foram revogados com sucesso")