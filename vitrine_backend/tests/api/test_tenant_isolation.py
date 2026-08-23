"""Testes de isolamento entre empresas (tenants) — Fase 1 do plano de SaaS.

Cria DUAS empresas, cada uma com seus próprios usuários/dados, e verifica
que nenhuma delas consegue ler, listar ou escrever dado da outra através
da API. Este é o risco de segurança #1 em qualquer retrofit de
multi-tenancy: basta UM filtro de empresa esquecido em UMA query para
vazar dado entre clientes — por isso o teste cobre os módulos mais
sensíveis (produtos, usuários, configurações, inventário) em vez de só
o feliz-caminho de "cada empresa vê a si mesma".
"""

import pytest
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from app.application.utils.security import hash_password


@pytest.fixture
def empresa_b(db_session):
    empresa = Empresa(nome="Empresa B", slug="empresa-b", status="ativa")
    db_session.add(empresa)
    db_session.commit()
    db_session.refresh(empresa)
    return empresa


@pytest.fixture
def usuario_admin_b(db_session, empresa_b):
    user = Usuario(
        username="admin_b",
        nome_exibicao="Admin da Empresa B",
        role="admin",
        hashed_password=hash_password("senha123"),
        token_version=0,
        empresa_id=empresa_b.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _token(client, username: str, password: str = "senha123") -> str:
    resp = client.post("/auth/token", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def token_admin_b(client, usuario_admin_b):
    return _token(client, "admin_b")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestIsolamentoProdutos:
    def test_empresa_b_nao_ve_produto_da_empresa_a(
        self, client, db_session, empresa_padrao, empresa_b, token_admin, token_admin_b
    ):
        from app.domain.models.produto import Produto, ProdutoCodigo

        db_session.add(Produto(
            empresa_id=empresa_padrao.id, codigo_chamada="000999", nome="Produto da Empresa A",
            grupo="G", familia="F", preco_venda=10.0, preco_custo=5.0, estoque=1.0,
        ))
        db_session.add(ProdutoCodigo(empresa_id=empresa_padrao.id, codigo="7891234567895", codigo_chamada="000999"))
        db_session.commit()

        # Empresa A enxerga o próprio produto.
        resp_a = client.get("/produtos/", headers=_auth(token_admin))
        assert resp_a.status_code == 200
        assert any(p["codigo_chamada"] == "000999" for p in resp_a.json())

        # Empresa B não vê nada — nem na listagem, nem na busca direta por código.
        resp_b = client.get("/produtos/", headers=_auth(token_admin_b))
        assert resp_b.status_code == 200
        assert resp_b.json() == []

        resp_b_direto = client.get("/produtos/000999", headers=_auth(token_admin_b))
        assert resp_b_direto.status_code == 404

        resp_b_barcode = client.get("/produtos/7891234567895", headers=_auth(token_admin_b))
        assert resp_b_barcode.status_code == 404

    def test_empresa_b_nao_ve_produto_de_a_na_busca_por_nome(
        self, client, db_session, empresa_padrao, token_admin_b
    ):
        from app.domain.models.produto import Produto

        db_session.add(Produto(
            empresa_id=empresa_padrao.id, codigo_chamada="P-NOME", nome="ProdutoUnicoDaEmpresaA",
            grupo="G", familia="F", preco_venda=10.0, preco_custo=5.0, estoque=1.0,
        ))
        db_session.commit()

        resp = client.get("/produtos/busca", params={"nome": "ProdutoUnicoDaEmpresaA"}, headers=_auth(token_admin_b))
        assert resp.status_code == 200
        assert resp.json() == []


class TestIsolamentoUsuarios:
    def test_empresa_b_nao_lista_usuarios_de_a(self, client, usuario_admin, token_admin_b):
        resp = client.get("/auth/usuarios", headers=_auth(token_admin_b))
        assert resp.status_code == 200
        usernames = [u["username"] for u in resp.json()]
        assert usuario_admin.username not in usernames

    def test_empresa_b_nao_edita_usuario_de_a(self, client, usuario_operador, token_admin_b):
        resp = client.patch(
            f"/auth/usuarios/{usuario_operador.id}",
            json={"role": "admin"},
            headers=_auth(token_admin_b),
        )
        # 404, não 403: não deve nem revelar que o ID existe em outro tenant.
        assert resp.status_code == 404

    def test_empresa_b_nao_exclui_usuario_de_a(self, client, usuario_operador, token_admin_b):
        resp = client.delete(f"/auth/usuarios/{usuario_operador.id}", headers=_auth(token_admin_b))
        assert resp.status_code == 404


class TestIsolamentoConfiguracoes:
    def test_configuracao_de_a_nao_aparece_para_b(self, client, token_admin, token_admin_b):
        set_resp = client.patch(
            "/admin/configuracoes",
            json={"valores": {"nome_estabelecimento": "Loja da Empresa A"}},
            headers=_auth(token_admin),
        )
        assert set_resp.status_code == 200

        resp_b = client.get("/admin/configuracoes", headers=_auth(token_admin_b))
        assert resp_b.status_code == 200
        # B nunca configurou nada — não deve herdar o valor de A.
        assert resp_b.json()["configuracoes"].get("nome_estabelecimento", "") != "Loja da Empresa A"

    def test_empresas_podem_ter_o_mesmo_nome_de_chave_com_valores_diferentes(
        self, client, token_admin, token_admin_b
    ):
        client.patch(
            "/admin/configuracoes",
            json={"valores": {"nome_estabelecimento": "Loja A"}},
            headers=_auth(token_admin),
        )
        client.patch(
            "/admin/configuracoes",
            json={"valores": {"nome_estabelecimento": "Loja B"}},
            headers=_auth(token_admin_b),
        )

        valor_a = client.get("/admin/configuracoes", headers=_auth(token_admin)).json()["configuracoes"]["nome_estabelecimento"]
        valor_b = client.get("/admin/configuracoes", headers=_auth(token_admin_b)).json()["configuracoes"]["nome_estabelecimento"]

        assert valor_a == "Loja A"
        assert valor_b == "Loja B"


class TestIsolamentoInventario:
    def test_empresa_b_nao_lista_sessao_de_a(self, client, token_admin, token_admin_b):
        criar = client.post(
            "/admin/inventario/sessoes", json={"nome": "Sessão da Empresa A"}, headers=_auth(token_admin)
        )
        assert criar.status_code == 201

        resp_b = client.get("/admin/inventario/sessoes", headers=_auth(token_admin_b))
        assert resp_b.status_code == 200
        nomes = [s["nome"] for s in resp_b.json()]
        assert "Sessão da Empresa A" not in nomes

    def test_codigo_convite_de_a_nao_funciona_para_b(self, client, token_admin, token_admin_b):
        """Ponto crítico: um código de convite vazado/adivinhado de outra
        empresa não deve permitir entrar na sessão dela."""
        criar = client.post(
            "/admin/inventario/sessoes", json={"nome": "Sessão Privada A"}, headers=_auth(token_admin)
        )
        codigo = criar.json()["codigo_convite"]

        resp_b = client.post(
            "/admin/inventario/sessoes/entrar", json={"codigo_convite": codigo}, headers=_auth(token_admin_b)
        )
        assert resp_b.status_code == 404

    def test_empresa_b_nao_acessa_sessao_de_a_por_id(self, client, token_admin, token_admin_b):
        criar = client.post(
            "/admin/inventario/sessoes", json={"nome": "Sessão A"}, headers=_auth(token_admin)
        )
        sid = criar.json()["id"]

        resp_b = client.get(f"/admin/inventario/sessoes/{sid}/itens", headers=_auth(token_admin_b))
        assert resp_b.status_code == 404


class TestIsolamentoContatos:
    def test_contato_email_de_a_nao_aparece_para_b(self, client, token_admin, token_admin_b):
        criar = client.post(
            "/admin/email/contatos",
            json={"email": "a@empresaA.com", "nome": "Contato A"},
            headers=_auth(token_admin),
        )
        assert criar.status_code == 201

        resp_b = client.get("/admin/email/contatos", headers=_auth(token_admin_b))
        assert resp_b.status_code == 200
        assert resp_b.json() == []

    def test_empresa_b_nao_edita_contato_whatsapp_de_a(self, client, token_admin, token_admin_b):
        criar = client.post(
            "/admin/whatsapp/contatos",
            json={"numero": "11999990000", "nome": "Contato A"},
            headers=_auth(token_admin),
        )
        contato_id = criar.json()["id"]

        resp_b = client.put(
            f"/admin/whatsapp/contatos/{contato_id}",
            json={"numero": "11888880000", "nome": "Sequestrado"},
            headers=_auth(token_admin_b),
        )
        assert resp_b.status_code == 404


class TestIsolamentoSync:
    def test_empresa_b_nao_ve_historico_de_sync_de_a(self, client, db_session, empresa_padrao, token_admin, token_admin_b):
        from app.domain.models.sync_job import SyncJob
        from datetime import datetime, timezone

        db_session.add(SyncJob(
            empresa_id=empresa_padrao.id, job_id="job-empresa-a",
            status="sucesso", started_at=datetime.now(timezone.utc),
        ))
        db_session.commit()

        resp_a = client.get("/admin/sync", headers=_auth(token_admin))
        assert any(j["job_id"] == "job-empresa-a" for j in resp_a.json()["jobs"])

        resp_b = client.get("/admin/sync", headers=_auth(token_admin_b))
        assert resp_b.json()["jobs"] == []
        assert resp_b.json()["total"] == 0

        # Status individual: B não consegue nem confirmar que o job existe.
        resp_status_b = client.get("/admin/sync/job-empresa-a", headers=_auth(token_admin_b))
        assert resp_status_b.status_code == 404
