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
        """Busca GLOBAL (sem filtro de empresa) — usada só no login.

        O login não tem seletor de tenant; é a busca por username que
        resolve a empresa do usuário (ver Usuario.empresa_id). Nenhum
        outro método deste repositório deve ficar sem filtro de empresa.
        """
        with temporizador("SQL usuario.buscar_por_username", logger):
            stmt = select(Usuario).where(Usuario.username == username)
            return self._session.execute(stmt).scalars().first()

    def buscar_por_id(self, usuario_id: int, empresa_id: int) -> Optional[Usuario]:
        """Busca escopada à empresa — um admin nunca enxerga usuário de outro tenant.

        Retorna None (não uma exceção) se o usuário existir mas for de
        outra empresa — o caller trata isso como 404, sem revelar que o
        ID existe em outro tenant.
        """
        with temporizador("SQL usuario.buscar_por_id", logger):
            stmt = select(Usuario).where(
                Usuario.id == usuario_id, Usuario.empresa_id == empresa_id
            )
            return self._session.execute(stmt).scalars().first()

    def listar(self, empresa_id: int) -> List[Usuario]:
        with temporizador("SQL usuario.listar", logger):
            stmt = (
                select(Usuario)
                .where(Usuario.empresa_id == empresa_id)
                .order_by(Usuario.id)
            )
            resultado = list(self._session.execute(stmt).scalars().all())
        logger.info("UsuarioRepository.listar | empresa_id=%s rows=%s", empresa_id, len(resultado))
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