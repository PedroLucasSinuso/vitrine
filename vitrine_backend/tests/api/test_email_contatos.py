import pytest


class TestEmailContatos:
    def test_criar_contato(self, client, token_supervisor):
        resp = client.post(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "george@example.com", "nome": "George"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "george@example.com"
        assert data["nome"] == "George"
        assert "id" in data

    def test_listar_contatos(self, client, token_supervisor):
        client.post(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "george@example.com", "nome": "George"},
        )
        client.post(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "carlos@example.com", "nome": "Carlos"},
        )
        resp = client.get(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["nome"] == "Carlos"
        assert data[1]["nome"] == "George"

    def test_atualizar_contato(self, client, token_supervisor):
        criado = client.post(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "george@example.com", "nome": "George"},
        ).json()
        resp = client.put(
            f"/admin/email/contatos/{criado['id']}",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "jorge@example.com", "nome": "Jorge"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "jorge@example.com"
        assert data["nome"] == "Jorge"

    def test_remover_contato(self, client, token_supervisor):
        criado = client.post(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "george@example.com", "nome": "George"},
        ).json()
        resp = client.delete(
            f"/admin/email/contatos/{criado['id']}",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 204
        lista = client.get(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        ).json()
        assert len(lista) == 0

    def test_remover_contato_inexistente(self, client, token_supervisor):
        resp = client.delete(
            "/admin/email/contatos/999",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contato não encontrado"

    def test_atualizar_contato_inexistente(self, client, token_supervisor):
        resp = client.put(
            "/admin/email/contatos/999",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"email": "nada@nada.com", "nome": "Ninguem"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contato não encontrado"

    def test_criar_contato_sem_auth(self, client):
        resp = client.post(
            "/admin/email/contatos",
            json={"email": "george@example.com", "nome": "George"},
        )
        assert resp.status_code == 401

    def test_criar_contato_como_operador(self, client, token_operador):
        resp = client.post(
            "/admin/email/contatos",
            headers={"Authorization": f"Bearer {token_operador}"},
            json={"email": "george@example.com", "nome": "George"},
        )
        assert resp.status_code == 403
