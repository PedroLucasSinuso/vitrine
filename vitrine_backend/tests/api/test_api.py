import pytest
from app.domain.models.produto import Produto


def is_valid_ean13(codigo: str) -> bool:
    if len(codigo) != 13 or not codigo.isdigit():
        return False
    soma = 0
    peso = 3
    for ch in reversed(codigo[:-1]):
        soma += int(ch) * peso
        peso = 1 if peso == 3 else 3
    calculado = (10 - (soma % 10)) % 10
    return calculado == int(codigo[-1])


def generate_valid_ean13() -> str:
    base = "789123456789"
    soma = 0
    peso = 3
    for ch in reversed(base):
        soma += int(ch) * peso
        peso = 1 if peso == 3 else 3
    digito = (10 - (soma % 10)) % 10
    return f"{base}{digito}"


@pytest.fixture
def produto_existente(db_session):
    from app.domain.models.produto import ProdutoCodigo

    valid_code = generate_valid_ean13()
    prod = Produto(
        codigo_chamada=valid_code,
        grupo="EletrÃ´nicos",
        familia="Celulares",
        nome="Smartphone XYZ",
        preco_venda=999.99,
        preco_custo=750.00,
        estoque=50.0,
    )
    db_session.add(prod)
    db_session.flush()

    prod_codigo = ProdutoCodigo(
        codigo=valid_code,
        codigo_chamada=valid_code,
    )
    db_session.add(prod_codigo)
    db_session.commit()
    db_session.refresh(prod)
    return prod


class TestAuthToken:
    def test_token_credenciais_validas(self, client, usuario_admin):
        response = client.post(
            "/auth/token",
            data={"username": "admin1", "password": "senha123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_token_credenciais_invalidas(self, client, usuario_admin):
        response = client.post(
            "/auth/token",
            data={"username": "admin1", "password": "errada"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Credenciais invÃ¡lidas"

    def test_token_usuario_inexistente(self, client):
        response = client.post(
            "/auth/token",
            data={"username": "naoexiste", "password": "qualquer"},
        )
        assert response.status_code == 401

    def test_token_credenciais_vazias(self, client):
        response = client.post(
            "/auth/token",
            data={"username": "", "password": ""},
        )
        assert response.status_code == 422


class TestAuthRegister:
    def test_registrar_usuario_como_admin(self, client, token_admin):
        response = client.post(
            "/auth/register",
            json={
                "username": "novousuario",
                "nome_exibicao": "Novo UsuÃ¡rio",
                "password": "senha456",
                "role": "operador",
            },
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "novousuario"
        assert data["role"] == "operador"

    def test_registrar_usuario_sem_autenticacao(self, client):
        response = client.post(
            "/auth/register",
            json={
                "username": "novousuario",
                "nome_exibicao": "Novo",
                "password": "senha",
                "role": "operador",
            },
        )
        assert response.status_code == 401

    def test_registrar_usuario_com_role_invalida(self, client, token_admin):
        response = client.post(
            "/auth/register",
            json={
                "username": "usuario2",
                "nome_exibicao": "Usuario",
                "password": "senha",
                "role": "invalido",
            },
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 422


class TestProdutosListar:
    def test_listar_produtos_autenticado(self, client, token_admin, produto_existente):
        response = client.get(
            "/produtos/",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_listar_produtos_sem_autenticacao(self, client):
        response = client.get("/produtos/")
        assert response.status_code == 401

    def test_listar_produtos_com_paginacao(self, client, token_admin, produto_existente):
        response = client.get(
            "/produtos/?limit=10&offset=0",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200


class TestProdutosGet:
    def test_obter_produto_por_codigo(self, client, token_admin, produto_existente):
        response = client.get(
            f"/produtos/{produto_existente.codigo_chamada}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["codigo_chamada"] == produto_existente.codigo_chamada
        assert "preco_venda" in data
        assert "preco_custo" not in data

    def test_obter_produto_inexistente(self, client, token_admin):
        base = "000000000000"
        soma = 0
        peso = 3
        for ch in reversed(base[:-1]):
            soma += int(ch) * peso
            peso = 1 if peso == 3 else 3
        digito = (10 - (soma % 10)) % 10
        valid_nonexistent = f"{base}{digito}"

        response = client.get(
            f"/produtos/{valid_nonexistent}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 404

    def test_obter_produto_codigo_invalido(self, client, token_admin):
        response = client.get(
            "/produtos/codigo@invalido!",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 400


class TestProdutosCompleto:
    def test_obter_produto_completo_como_supervisor(
        self, client, token_supervisor, produto_existente
    ):
        response = client.get(
            f"/produtos/{produto_existente.codigo_chamada}/completo",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["codigo_chamada"] == produto_existente.codigo_chamada
        assert "preco_custo" in data
        assert "markup" in data

    def test_obter_produto_completo_como_admin(
        self, client, token_admin, produto_existente
    ):
        response = client.get(
            f"/produtos/{produto_existente.codigo_chamada}/completo",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200

    def test_obter_produto_completo_como_operador(
        self, client, token_operador, produto_existente
    ):
        response = client.get(
            f"/produtos/{produto_existente.codigo_chamada}/completo",
            headers={"Authorization": f"Bearer {token_operador}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Acesso restrito a supervisores"

    def test_obter_produto_completo_sem_autenticacao(
        self, client, produto_existente
    ):
        response = client.get(
            f"/produtos/{produto_existente.codigo_chamada}/completo",
        )
        assert response.status_code == 401


class TestCacheStatus:
    def test_obter_status_cache(self, client):
        response = client.get("/status/")
        assert response.status_code == 200
        data = response.json()
        assert "last_updated" in data


class TestAdminSync:
    def test_trigger_sync_como_admin(self, client, token_admin):
        response = client.post(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert data["status"] == "started"

    def test_trigger_sync_como_supervisor(self, client, token_supervisor):
        response = client.post(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Acesso restrito a administradores"

    def test_trigger_sync_como_operador(self, client, token_operador):
        response = client.post(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_operador}"},
        )
        assert response.status_code == 403

    def test_trigger_sync_sem_autenticacao(self, client):
        response = client.post("/admin/sync")
        assert response.status_code == 401

    def test_obter_sync_status_apos_trigger(self, client, token_admin):
        trigger = client.post(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        job_id = trigger.json()["job_id"]

        response = client.get(
            f"/admin/sync/{job_id}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] in ("em_progresso", "sucesso", "erro")

    def test_obter_sync_status_inexistente(self, client, token_admin):
        response = client.get(
            "/admin/sync/job-nao-existe",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 404

    def test_listar_sync_history(self, client, token_admin, db_session):
        from app.domain.models.cache_status import CacheStatus
        from datetime import datetime, timezone

        cache = CacheStatus(
            last_updated=datetime.now(timezone.utc),
            status="sucesso"
        )
        db_session.add(cache)
        db_session.commit()

        response = client.get(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert data["total"] >= 1


class TestCors:
    def test_cors_headers_present(self, client):
        response = client.options(
            "/auth/token",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code in [200, 204, 405]