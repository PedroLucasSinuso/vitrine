import pytest


class TestWhatsAppContatos:
    def test_criar_contato(self, client, token_supervisor):
        resp = client.post(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5522999999999", "nome": "George"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["numero"] == "5522999999999"
        assert data["nome"] == "George"
        assert "id" in data

    def test_listar_contatos(self, client, token_supervisor):
        client.post(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5522999999999", "nome": "George"},
        )
        client.post(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5521988888888", "nome": "Carlos"},
        )
        resp = client.get(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["nome"] == "Carlos"
        assert data[1]["nome"] == "George"

    def test_atualizar_contato(self, client, token_supervisor):
        criado = client.post(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5522999999999", "nome": "George"},
        ).json()
        resp = client.put(
            f"/admin/whatsapp/contatos/{criado['id']}",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5522000000000", "nome": "Jorge"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["numero"] == "5522000000000"
        assert data["nome"] == "Jorge"

    def test_remover_contato(self, client, token_supervisor):
        criado = client.post(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5522999999999", "nome": "George"},
        ).json()
        resp = client.delete(
            f"/admin/whatsapp/contatos/{criado['id']}",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 204
        lista = client.get(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        ).json()
        assert len(lista) == 0

    def test_contato_inexistente(self, client, token_supervisor):
        resp = client.get(
            "/admin/whatsapp/contatos/999",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 405

    def test_remover_contato_inexistente(self, client, token_supervisor):
        resp = client.delete(
            "/admin/whatsapp/contatos/999",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contato não encontrado"

    def test_atualizar_contato_inexistente(self, client, token_supervisor):
        resp = client.put(
            "/admin/whatsapp/contatos/999",
            headers={"Authorization": f"Bearer {token_supervisor}"},
            json={"numero": "5522000000000", "nome": "Ninguem"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Contato não encontrado"

    def test_criar_contato_sem_auth(self, client):
        resp = client.post(
            "/admin/whatsapp/contatos",
            json={"numero": "5522999999999", "nome": "George"},
        )
        assert resp.status_code == 401

    def test_criar_contato_como_operador(self, client, token_operador):
        resp = client.post(
            "/admin/whatsapp/contatos",
            headers={"Authorization": f"Bearer {token_operador}"},
            json={"numero": "5522999999999", "nome": "George"},
        )
        assert resp.status_code == 403
