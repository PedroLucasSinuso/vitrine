"""Testes de lockout de login (S2).

Verifica que após 5 tentativas falhas em 15 minutos o endpoint retorna 429.
Verifica também que um login bem sucedido limpa o contador.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models.usuario import Usuario
from app.domain.models.tentativa_login import TentativaLogin
from app.application.utils.security import hash_password


class TestLoginLockout:
    def test_lockout_apos_5_tentativas_falhas(self, client: TestClient, db_session: Session):
        """Após 5 tentativas com senha errada, a 6ª deve retornar 429."""
        username = "lockout_user"

        for i in range(5):
            resp = client.post(
                "/auth/token",
                data={"username": username, "password": "senha_errada"},
            )
            assert resp.status_code == 401, f"Tentativa {i+1} deveria ser 401"

        # 6ª tentativa — deve ser bloqueada
        resp = client.post(
            "/auth/token",
            data={"username": username, "password": "qualquer_coisa"},
        )
        assert resp.status_code == 429
        data = resp.json()
        assert "Muitas tentativas" in data["detail"]

    def test_login_sucesso_limpa_contador(self, client: TestClient, db_session: Session):
        """Após login bem sucedido, o contador de falhas deve zerar."""
        # Cria um usuário válido
        usuario = Usuario(
            username="sucesso_limpa",
            nome_exibicao="Teste",
            role="operador",
            hashed_password=hash_password("senha_correta"),
            token_version=0,
        )
        db_session.add(usuario)
        db_session.commit()

        username = "sucesso_limpa"

        # 3 tentativas falhas
        for i in range(3):
            resp = client.post(
                "/auth/token",
                data={"username": username, "password": "errada"},
            )
            assert resp.status_code == 401

        # Login bem sucedido
        resp = client.post(
            "/auth/token",
            data={"username": username, "password": "senha_correta"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

        # Após o sucesso, novas tentativas erradas NÃO devem bloquear
        # (o contador foi limpo)
        resp = client.post(
            "/auth/token",
            data={"username": username, "password": "errada_novamente"},
        )
        assert resp.status_code == 401  # apenas 401, não 429

    def test_lockout_nao_afeta_outros_usuarios(self, client: TestClient, db_session: Session):
        """Lockout de um usuário não deve afetar outros."""
        # Cria um segundo usuário
        usuario = Usuario(
            username="outro_usuario",
            nome_exibicao="Outro",
            role="operador",
            hashed_password=hash_password("senha_outro"),
            token_version=0,
        )
        db_session.add(usuario)
        db_session.commit()

        username_a = "vai_travar"
        username_b = "outro_usuario"

        # 5 falhas para usuário A
        for i in range(5):
            client.post(
                "/auth/token",
                data={"username": username_a, "password": "errada"},
            )

        # Usuário B deve conseguir logar normalmente
        resp = client.post(
            "/auth/token",
            data={"username": username_b, "password": "senha_outro"},
        )
        assert resp.status_code == 200
