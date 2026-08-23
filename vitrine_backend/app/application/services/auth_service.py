from typing import List
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import UsuarioCreate, UsuarioPatch
from app.application.utils.security import hash_password, verify_password
from app.application.utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)


class AuthService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def autenticar(self, username: str, password: str) -> tuple[str, str]:
        """Retorna (access_token, refresh_token).

        ``buscar_por_username`` é intencionalmente global (não filtrado por
        empresa) — o login não tem seletor de tenant, então a busca por
        username já resolve a empresa do usuário (ver comentário em
        app/domain/models/usuario.py). O ``empresa_id`` resolvido aqui é o
        que vai no token e passa a escopar todo o resto da sessão.
        """
        usuario = self.repo.buscar_por_username(username)
        if not usuario or not verify_password(password, usuario.hashed_password):
            raise ValueError("Credenciais inválidas")
        payload = {"sub": usuario.username, "role": usuario.role, "nome_exibicao": usuario.nome_exibicao}
        access = create_access_token(
            payload, user_id=usuario.id, token_version=usuario.token_version, empresa_id=usuario.empresa_id
        )
        refresh = create_refresh_token(
            {"sub": usuario.username},
            user_id=usuario.id,
            token_version=usuario.token_version,
            empresa_id=usuario.empresa_id,
        )
        return access, refresh

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Valida um refresh token e emite NOVO par (access_token, refresh_token).

        Verifica: assinatura, expiração, type == 'refresh' e token_version.
        """
        try:
            payload = decode_access_token(refresh_token)
        except ValueError:
            raise ValueError("Refresh token inválido ou expirado")

        if payload.get("type") != "refresh":
            raise ValueError("Token não é um refresh token")

        username = payload.get("sub")
        if not username:
            raise ValueError("Refresh token inválido: sub ausente")

        usuario = self.repo.buscar_por_username(username)
        if not usuario:
            raise ValueError("Usuário não encontrado")

        # Verifica token_version (logout-all)
        token_version = payload.get("token_version", 0)
        if token_version < usuario.token_version:
            raise ValueError("Refresh token revogado (logout-all)")

        # Emite NOVO par com rotação
        new_payload = {"sub": usuario.username, "role": usuario.role, "nome_exibicao": usuario.nome_exibicao}
        new_access = create_access_token(
            new_payload, user_id=usuario.id, token_version=usuario.token_version, empresa_id=usuario.empresa_id
        )
        new_refresh = create_refresh_token(
            {"sub": usuario.username},
            user_id=usuario.id,
            token_version=usuario.token_version,
            empresa_id=usuario.empresa_id,
        )
        return new_access, new_refresh

    def registrar(self, dados: UsuarioCreate, empresa_id: int) -> Usuario:
        """Cria um usuário DENTRO da empresa do admin que está registrando.

        ``empresa_id`` vem sempre do token do admin autenticado (nunca do
        corpo da requisição) — impede que alguém crie um usuário em outro
        tenant manipulando o payload.
        """
        if self.repo.buscar_por_username(dados.username):
            raise ValueError(f"Username '{dados.username}' já está em uso")
        usuario = Usuario(
            username=dados.username,
            nome_exibicao=dados.nome_exibicao,
            role=dados.role,
            hashed_password=hash_password(dados.password),
            empresa_id=empresa_id,
        )
        return self.repo.criar(usuario)

    def listar(self, empresa_id: int) -> List[Usuario]:
        return self.repo.listar(empresa_id)

    def atualizar(self, usuario_id: int, dados: UsuarioPatch, empresa_id: int) -> Usuario:
        usuario = self.repo.buscar_por_id(usuario_id, empresa_id)
        if not usuario:
            raise LookupError(f"Usuário {usuario_id} não encontrado")
        if not dados.tem_alteracao():
            raise ValueError("Nenhuma alteração fornecida")
        if dados.password is not None:
            usuario.hashed_password = hash_password(dados.password)
        if dados.role is not None and dados.role != usuario.role:
            usuario.role = dados.role
            usuario.token_version += 1
        self.repo.atualizar(usuario)
        return usuario

    def excluir(self, usuario_id: int, admin_id: int, empresa_id: int) -> None:
        if usuario_id == admin_id:
            raise PermissionError("Não é possível excluir o próprio usuário")
        usuario = self.repo.buscar_por_id(usuario_id, empresa_id)
        if not usuario:
            raise LookupError(f"Usuário {usuario_id} não encontrado")
        self.repo.excluir(usuario)