"""E2E tests for JWT refresh token flow.

Cobre:
- Login retorna access + refresh tokens
- Refresh com refresh token válido retorna NOVO par (rotação)
- Refresh token expirado → 401
- Access token enviado como refresh → 401
- Token com type != 'refresh' → 401
- Refresh após logout-all → 401
- Refresh após mudança de role → 401 (token_version incrementado)
- /auth/token ainda funciona (backward compat)
"""

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.application.utils.jwt_handler import create_refresh_token, create_access_token


# ── Helpers ───────────────────────────────────────────────────────────────────

def _login(client: TestClient, username: str = "admin1", password: str = "senha123") -> dict:
    """Faz login e retorna o body da resposta."""
    resp = client.post("/auth/token", data={"username": username, "password": password})
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()


def _criar_token_expirado(username: str, user_id: int = 1, token_version: int = 0) -> str:
    """Cria um refresh token JWT já expirado."""
    payload = {
        "sub": username,
        "iat": datetime.now(timezone.utc) - timedelta(hours=1),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),  # já expirou
        "jti": "expired-test-jti",
        "user_id": user_id,
        "token_version": token_version,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRefreshTokenE2E:
    """End-to-end tests for the refresh token flow."""

    def test_login_retorna_tokens(self, client, db_session, usuario_admin):
        """Login deve retornar access_token e refresh_token."""
        data = _login(client)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # Ambos devem ser JWT válidos
        decoded_access = jwt.decode(data["access_token"], settings.jwt_secret, algorithms=["HS256"])
        decoded_refresh = jwt.decode(data["refresh_token"], settings.jwt_secret, algorithms=["HS256"])
        assert decoded_access["type"] == "access"
        assert decoded_refresh["type"] == "refresh"
        assert decoded_access["sub"] == "admin1"
        assert decoded_refresh["sub"] == "admin1"

    def test_refresh_retorna_novo_par(self, client, db_session, usuario_admin):
        """Refresh com token válido retorna NOVO par (access + refresh)."""
        data = _login(client)
        old_access = data["access_token"]
        old_refresh = data["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 200, f"Refresh falhou: {resp.text}"
        new_data = resp.json()

        assert "access_token" in new_data
        assert "refresh_token" in new_data
        # O novo access token deve ser DIFERENTE do antigo (rotação)
        assert new_data["access_token"] != old_access
        assert new_data["refresh_token"] != old_refresh

        # Verificar que o novo access token funciona
        resp2 = client.get("/status/", headers={"Authorization": f"Bearer {new_data['access_token']}"})
        assert resp2.status_code == 200, "Novo access token não funciona"

    def test_refresh_token_expirado_retorna_401(self, client, db_session, usuario_admin):
        """Refresh token expirado deve retornar 401."""
        expired = _criar_token_expirado("admin1", user_id=usuario_admin.id, token_version=usuario_admin.token_version)
        resp = client.post("/auth/refresh", json={"refresh_token": expired})
        assert resp.status_code == 401
        assert "inválido" in resp.text.lower() or "expirado" in resp.text.lower()

    def test_access_token_como_refresh_retorna_401(self, client, db_session, usuario_admin):
        """Access token usado como refresh deve retornar 401 (type != refresh)."""
        data = _login(client)
        access_token = data["access_token"]
        resp = client.post("/auth/refresh", json={"refresh_token": access_token})
        assert resp.status_code == 401
        assert "não é um refresh token" in resp.text.lower() or "inválido" in resp.text.lower()

    def test_refresh_apos_logout_all_retorna_401(self, client, db_session, usuario_admin):
        """Após logout-all, token_version aumenta e refresh antigo deve falhar."""
        data = _login(client)
        refresh_token = data["refresh_token"]

        # Fazer logout-all (incrementa token_version)
        resp = client.post(
            "/auth/logout-all",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        assert resp.status_code == 200

        # Tentar refresh com o token antigo
        resp2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp2.status_code == 401
        assert "revogado" in resp2.text.lower()

    def test_refresh_apos_mudanca_de_role_retorna_401(self, client, db_session, usuario_admin, token_admin):
        """Mudança de role incrementa token_version → refresh antigo inválido."""
        data = _login(client)
        refresh_token = data["refresh_token"]

        # Mudar role do usuário (via admin)
        resp = client.patch(
            f"/auth/usuarios/{usuario_admin.id}",
            json={"role": "supervisor"},
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 200

        # Tentar refresh com token antigo
        resp2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp2.status_code == 401
        assert "revogado" in resp2.text.lower()

    def test_refresh_rotaciona_mantendo_sessao(self, client, db_session, usuario_admin):
        """Múltiplos refreshes consecutivos devem funcionar (cadeia)."""
        data = _login(client)

        for i in range(3):
            resp = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
            assert resp.status_code == 200, f"Refresh {i+1} falhou: {resp.text}"
            data = resp.json()

        # Após 3 refreshes, o refresh inicial já não funciona (foi substituído)
        # O último refresh deve funcionar
        resp_final = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
        assert resp_final.status_code == 200

    def test_auth_token_ainda_funciona(self, client, db_session, usuario_admin):
        """POST /auth/token continua funcionando como antes (backward compat)."""
        resp = client.post("/auth/token", data={"username": "admin1", "password": "senha123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data
        # Testar que o token funciona
        resp2 = client.get("/status/", headers={"Authorization": f"Bearer {data['access_token']}"})
        assert resp2.status_code == 200
