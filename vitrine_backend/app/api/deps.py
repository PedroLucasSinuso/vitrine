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