import pytest
from app.application.services.auth_service import AuthService
from app.application.utils.security import hash_password
from app.domain.models.usuario import Usuario
from app.schemas.usuario_schema import UsuarioCreate


class FakeUsuarioRepository:
    def __init__(self, usuario=None):
        self._usuario = usuario
        self.criado = None

    def buscar_por_username(self, username: str):
        if self._usuario and self._usuario.username == username:
            return self._usuario
        return None

    def criar(self, usuario: Usuario) -> Usuario:
        self.criado = usuario
        return usuario


@pytest.fixture
def usuario_existente():
    return Usuario(
        id=1,
        username="supervisor1",
        nome_exibicao="Supervisor",
        role="supervisor",
        hashed_password=hash_password("senha123"),
    )


def test_autenticar_credenciais_validas(usuario_existente):
    repo = FakeUsuarioRepository(usuario=usuario_existente)
    token = AuthService(repo).autenticar("supervisor1", "senha123")
    assert isinstance(token, str) and len(token) > 0


def test_autenticar_senha_errada(usuario_existente):
    repo = FakeUsuarioRepository(usuario=usuario_existente)
    with pytest.raises(ValueError):
        AuthService(repo).autenticar("supervisor1", "errada")


def test_autenticar_usuario_inexistente():
    repo = FakeUsuarioRepository(usuario=None)
    with pytest.raises(ValueError):
        AuthService(repo).autenticar("naoexiste", "qualquer")


def test_registrar_novo_usuario():
    repo = FakeUsuarioRepository(usuario=None)
    dados = UsuarioCreate(
        username="op1",
        nome_exibicao="Operador",
        password="senha123",
        role="operador",
    )
    usuario = AuthService(repo).registrar(dados)
    assert usuario.username == "op1"
    assert usuario.role == "operador"
    assert usuario.hashed_password != "senha123"


def test_registrar_username_duplicado(usuario_existente):
    repo = FakeUsuarioRepository(usuario=usuario_existente)
    dados = UsuarioCreate(
        username="supervisor1",
        nome_exibicao="Outro",
        password="senha",
        role="operador",
    )
    with pytest.raises(ValueError):
        AuthService(repo).registrar(dados)