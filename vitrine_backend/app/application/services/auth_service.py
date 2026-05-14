from typing import List
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import UsuarioCreate, UsuarioPatch
from app.application.utils.security import hash_password, verify_password
from app.application.utils.jwt_handler import create_access_token


class AuthService:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def autenticar(self, username: str, password: str) -> str:
        usuario = self.repo.buscar_por_username(username)
        if not usuario or not verify_password(password, usuario.hashed_password):
            raise ValueError("Credenciais inválidas")
        return create_access_token({"sub": usuario.username, "role": usuario.role, "nome_exibicao": usuario.nome_exibicao})

    def registrar(self, dados: UsuarioCreate) -> Usuario:
        if self.repo.buscar_por_username(dados.username):
            raise ValueError(f"Username '{dados.username}' já está em uso")
        usuario = Usuario(
            username=dados.username,
            nome_exibicao=dados.nome_exibicao,
            role=dados.role,
            hashed_password=hash_password(dados.password),
        )
        return self.repo.criar(usuario)

    def listar(self) -> List[Usuario]:
        return self.repo.listar()

    def atualizar(self, usuario_id: int, dados: UsuarioPatch) -> Usuario:
        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError(f"Usuário {usuario_id} não encontrado")
        if not dados.tem_alteracao():
            raise ValueError("Nenhuma alteração fornecida")
        if dados.password is not None:
            usuario.hashed_password = hash_password(dados.password)
        if dados.role is not None:
            usuario.role = dados.role
        self.repo.atualizar(usuario)
        return usuario

    def excluir(self, usuario_id: int, admin_id: int) -> None:
        if usuario_id == admin_id:
            raise PermissionError("Não é possível excluir o próprio usuário")
        usuario = self.repo.buscar_por_id(usuario_id)
        if not usuario:
            raise LookupError(f"Usuário {usuario_id} não encontrado")
        self.repo.excluir(usuario)