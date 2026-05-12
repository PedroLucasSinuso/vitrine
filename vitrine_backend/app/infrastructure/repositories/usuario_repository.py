from typing import Optional, List
from sqlalchemy import select
from app.domain.models.usuario import Usuario
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


class UsuarioRepository:
    def __init__(self, session):
        self._session = session

    def buscar_por_username(self, username: str) -> Optional[Usuario]:
        with temporizador("SQL usuario.buscar_por_username", logger):
            stmt = select(Usuario).where(Usuario.username == username)
            return self._session.execute(stmt).scalars().first()

    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]:
        with temporizador("SQL usuario.buscar_por_id", logger):
            stmt = select(Usuario).where(Usuario.id == usuario_id)
            return self._session.execute(stmt).scalars().first()

    def listar(self) -> List[Usuario]:
        with temporizador("SQL usuario.listar", logger):
            stmt = select(Usuario).order_by(Usuario.id)
            resultado = list(self._session.execute(stmt).scalars().all())
        logger.info("UsuarioRepository.listar | rows=%s", len(resultado))
        return resultado

    def criar(self, usuario: Usuario) -> Usuario:
        logger.info("UsuarioRepository.criar | username=%s role=%s", usuario.username, usuario.role)
        self._session.add(usuario)
        self._session.flush()
        return usuario

    def atualizar(self, usuario: Usuario) -> None:
        logger.debug("UsuarioRepository.atualizar | id=%s username=%s", usuario.id, usuario.username)
        self._session.flush()

    def excluir(self, usuario: Usuario) -> None:
        logger.info("UsuarioRepository.excluir | id=%s username=%s", usuario.id, usuario.username)
        self._session.delete(usuario)
        self._session.flush()