from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db, require_admin
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.application.services.auth_service import AuthService
from app.schemas.auth_schema import TokenResponse
from app.schemas.usuario_schema import UsuarioCreate, UsuarioPatch, UsuarioResponse
from app.domain.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


@router.post("/token", response_model=TokenResponse)
def login(dados: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    service = AuthService(UsuarioRepository(db))
    try:
        token = service.autenticar(dados.username, dados.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Credenciais invÃ¡lidas")
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UsuarioResponse, status_code=201)
def register(dados: UsuarioCreate, db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
    service = AuthService(UsuarioRepository(db))
    try:
        usuario = service.registrar(dados)
        db.commit()
        return usuario
    except ValueError as e:
        logger.warning("Erro ao registrar usuario | Erro: %s", e)
        raise HTTPException(status_code=409, detail="Usuario ja existe ou dados invalidos")


@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db), _admin: Usuario = Depends(require_admin)):
    return AuthService(UsuarioRepository(db)).listar()


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioPatch,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    service = AuthService(UsuarioRepository(db))
    try:
        usuario = service.atualizar(usuario_id, dados)
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
        service.excluir(usuario_id, admin.id)
        db.commit()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))