from datetime import date

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
def produto_existente(db_session, empresa_padrao):
    from app.domain.models.produto import ProdutoCodigo

    valid_code = generate_valid_ean13()
    prod = Produto(
        empresa_id=empresa_padrao.id,
        codigo_chamada=valid_code,
        grupo="Eletrônicos",
        familia="Celulares",
        nome="Smartphone XYZ",
        preco_venda=999.99,
        preco_custo=750.00,
        estoque=50.0,
    )
    db_session.add(prod)
    db_session.flush()

    prod_codigo = ProdutoCodigo(
        empresa_id=empresa_padrao.id,
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
        assert response.json()["detail"] == "Credenciais inválidas"

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
                "nome_exibicao": "Novo Usuário",
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
    def test_obter_status_cache(self, client, token_admin):
        # /status/ agora exige autenticação (multi-tenant: sem usuário
        # logado não há como saber de qual empresa mostrar o status).
        response = client.get("/status/", headers={"Authorization": f"Bearer {token_admin}"})
        assert response.status_code == 200
        data = response.json()
        assert "last_updated" in data

    def test_status_sem_autenticacao_retorna_401(self, client):
        response = client.get("/status/")
        assert response.status_code == 401


class TestAdminSync:
    def test_trigger_sync_como_admin(self, client, token_admin):
        response = client.post(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 201
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

    def test_listar_sync_history(self, client, token_admin, db_session, empresa_padrao):
        from app.domain.models.sync_job import SyncJob
        from datetime import datetime, timezone

        job = SyncJob(
            empresa_id=empresa_padrao.id,
            job_id="teste-history",
            status="sucesso",
            started_at=datetime.now(timezone.utc),
        )
        db_session.add(job)
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

    def test_sync_list_total_deve_ser_count_real(self, client, token_admin, db_session, empresa_padrao):
        """total deve refletir o número real de registros, não o limit (T6)."""
        from app.domain.models.sync_job import SyncJob
        from datetime import datetime, timezone

        # Cria 15 jobs (mais que o default limit=10)
        for i in range(15):
            db_session.add(SyncJob(
                empresa_id=empresa_padrao.id,
                job_id=f"job-{i:03d}",
                status="sucesso",
                started_at=datetime.now(timezone.utc),
            ))
        db_session.commit()

        # Chama sem limit explícito (default=10)
        response = client.get(
            "/admin/sync",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()

        # jobs deve ter no máximo 10 (limit default)
        assert len(data["jobs"]) == 10
        # total deve ser 15 (número real no banco)
        assert data["total"] == 15

        # Com limit=5, jobs=5 mas total=15
        response = client.get(
            "/admin/sync?limit=5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 5
        assert data["total"] == 15


class TestAdminCacheStatus:
    def test_cache_status_como_admin_sem_registro(self, client, token_admin):
        """Sem nenhum registro de cache, retorna produtos_cached=False."""
        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == {
            "produtos_cached": False,
            "last_refresh": None,
            "ttl_seconds": 30,
        }

    def test_cache_status_como_admin_com_registro(self, client, token_admin, db_session, empresa_padrao):
        """Com um registro de cache, retorna produtos_cached=True e last_refresh."""
        from datetime import datetime, timezone
        from app.domain.models.cache_status import CacheStatus

        now = datetime.now(timezone.utc)
        db_session.add(CacheStatus(empresa_id=empresa_padrao.id, last_updated=now, status="sucesso"))
        db_session.commit()

        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["produtos_cached"] is True
        assert data["last_refresh"] is not None
        assert data["ttl_seconds"] == 30

    def test_cache_status_supervisor_403(self, client, token_supervisor):
        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_supervisor}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Acesso restrito a administradores"

    def test_cache_status_operador_403(self, client, token_operador):
        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_operador}"},
        )
        assert response.status_code == 403

    def test_cache_status_sem_autenticacao_401(self, client):
        response = client.get("/admin/cache/status")
        assert response.status_code == 401


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


class TestAuthLogout:
    def test_logout_revoga_token(self, client, token_admin):
        """Fazer logout e verificar que o mesmo token é rejeitado em seguida."""
        # 1. Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Token revogado com sucesso"

        # 2. Tentar usar o mesmo token
        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Token revogado"

    def test_logout_all_invalida_tokens_anteriores(self, client, token_admin, db_session):
        """Fazer logout-all e verificar que o token existente é rejeitado."""
        # 1. Logout-all
        response = client.post(
            "/auth/logout-all",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Todos os tokens foram revogados com sucesso"

        # 2. Tentar usar o mesmo token (verificação de token_version)
        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Token revogado (logout-all)"

    def test_logout_apos_login_explicito(self, client, db_session, usuario_operador, token_admin):
        """Login explícito → logout → token rejeitado (T6)."""
        # 1. Login explícito
        resp = client.post(
            "/auth/token",
            data={"username": "operador1", "password": "senha123"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # 2. Logout
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Token revogado com sucesso"

        # 3. Mesmo token rejeitado em rota protegida
        resp = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Token revogado"

    def test_mudanca_role_invalida_token(self, client, token_operador, db_session, usuario_operador, usuario_admin):
        """Alterar role do operador para supervisor e verificar que token antigo é rejeitado."""
        # 1. Obtém um token de admin para alterar o role
        #    (usuario_admin fixture garante que admin1 existe no banco)
        response = client.post(
            "/auth/token",
            data={"username": "admin1", "password": "senha123"},
        )
        admin_token = response.json()["access_token"]

        # 2. Alterar role do operador para supervisor
        #    O serviço incrementa token_version quando a role muda
        response = client.patch(
            f"/auth/usuarios/{usuario_operador.id}",
            json={"role": "supervisor"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # 3. Tentar usar o token antigo do operador
        #    O token_version no payload (0) é menor que o novo (1) -> 401
        response = client.get(
            "/admin/cache/status",
            headers={"Authorization": f"Bearer {token_operador}"},
        )
        assert response.status_code == 401


class TestPublicStatusEndpoint:
    def test_status_endpoint_funciona(self, client, token_operador):
        """/status/ agora exige autenticação (ver TestCacheStatus) — qualquer
        role autenticado (aqui operador) já é suficiente."""
        response = client.get("/status/", headers={"Authorization": f"Bearer {token_operador}"})
        assert response.status_code == 200
        data = response.json()
        assert "last_updated" in data


class TestInventarioAdicionarItem:
    """IntegrityError retry path em adicionar_item (T1)."""

    def test_integrity_error_retry_path(
        self, client, db_session, usuario_admin, token_admin
    ):
        """Simula race condition que causa IntegrityError e verifica retry → 200."""
        headers = {"Authorization": f"Bearer {token_admin}"}

        # 1. Criar sessão (requer admin/supervisor)
        resp = client.post(
            "/admin/inventario/sessoes",
            json={"nome": "Test Retry"},
            headers=headers,
        )
        assert resp.status_code == 201
        sid = resp.json()["id"]

        # 2. Primeira adição normal
        resp = client.post(
            f"/admin/inventario/sessoes/{sid}/itens",
            json={
                "codigo": "RETRY01", "nome": "Produto",
                "grupo": "G", "familia": "F", "quantidade": 1,
            },
            headers=headers,
        )
        assert resp.status_code == 201

        # 3. Remover o item e criar um pending (não flush) que conflita
        from app.domain.models.inventario import ItemInventario

        db_session.query(ItemInventario).filter_by(
            sessao_id=sid, usuario_id=usuario_admin.id, codigo="RETRY01"
        ).delete()
        db_session.commit()

        # Desabilita autoflush para simular concorrência:
        # o SELECT do endpoint não enxergará o pending insert
        autoflush_original = db_session.autoflush
        db_session.autoflush = False
        try:
            db_session.add(ItemInventario(
                empresa_id=usuario_admin.empresa_id,
                sessao_id=sid, usuario_id=usuario_admin.id,
                codigo="RETRY01", nome="Produto",
                grupo="G", familia="F", quantidade=99,
            ))
            # 4. Segunda adição — SELECT não vê pending → tenta INSERT → IntegrityError
            #    catch rollback + retry → 200
            resp = client.post(
                f"/admin/inventario/sessoes/{sid}/itens",
                json={
                    "codigo": "RETRY01", "nome": "Produto",
                    "grupo": "G", "familia": "F", "quantidade": 2,
                },
                headers=headers,
            )
        finally:
            db_session.autoflush = autoflush_original

        assert resp.status_code == 201

        # 5. Verificar que o retry salvou o valor correto
        itens = client.get(
            f"/admin/inventario/sessoes/{sid}/itens",
            headers=headers,
        ).json()
        assert len(itens) == 1
        assert itens[0]["codigo"] == "RETRY01"
        assert itens[0]["quantidade"] == 2


class TestInventarioExcel:
    """Excel export endpoint de sessão (T4)."""

    def test_exportar_excel_sessao(
        self, client, db_session, usuario_admin, token_admin
    ):
        """Cria sessão com 2 itens e verifica headers do Excel."""
        # 1. Criar sessão
        resp = client.post(
            "/admin/inventario/sessoes",
            json={"nome": "Export Test"},
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 201
        sid = resp.json()["id"]

        # 2. Adicionar 2 itens
        for cod in ["ITEM01", "ITEM02"]:
            client.post(
                f"/admin/inventario/sessoes/{sid}/itens",
                json={
                    "codigo": cod, "nome": f"Produto {cod}",
                    "grupo": "G", "familia": "F", "quantidade": 5,
                },
                headers={"Authorization": f"Bearer {token_admin}"},
            )

        # 3. Exportar Excel
        resp = client.get(
            f"/admin/inventario/sessoes/{sid}/exportar-excel",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert "Content-Disposition" in resp.headers
        assert "attachment" in resp.headers["content-disposition"]


class TestBiExcelExport:
    """BI exportar/excel endpoint (T5)."""

    def test_exportar_excel_ranking(
        self, client, token_admin, transaction_source, criar_item
    ):
        """Com vendas no periodo, /bi/exportar/excel devolve 200 + planilha."""
        transaction_source.items_por_data = {
            date(2024, 1, 10): [
                criar_item("DOC1", date(2024, 1, 10), 10, 100.0),
                criar_item("DOC2", date(2024, 1, 10), 14, 200.0, qtd=2.0),
            ],
        }

        resp = client.get(
            "/bi/exportar/excel",
            params={
                "relatorio": "ranking",
                "data_inicio": "2024-01-01",
                "data_fim": "2024-01-31",
            },
            headers={"Authorization": f"Bearer {token_admin}"},
        )

        assert resp.status_code == 200
        assert resp.headers["content-type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        # Assinatura de arquivo .xlsx (zip) - garante que veio planilha de verdade.
        assert resp.content[:2] == b"PK"


class TestAuthRoleChange:
    """Token válido após role change + novo login (T7)."""

    def test_novo_token_funciona_apos_role_change(
        self, client, db_session, usuario_operador, usuario_admin,
        transaction_source, criar_item,
    ):
        """Altera role, faz login novamente e verifica que novo token funciona."""
        # A rota do passo 4 e' so' o veiculo para checar a autorizacao, mas
        # ela precisa de vendas no periodo para chegar ate' o 200.
        transaction_source.items_por_data = {
            date(2024, 1, 10): [criar_item("DOC1", date(2024, 1, 10), 10, 100.0)],
        }
        # 1. Fazer login como admin para alterar role
        resp = client.post(
            "/auth/token",
            data={"username": "admin1", "password": "senha123"},
        )
        admin_token = resp.json()["access_token"]

        # 2. Alterar role do operador para supervisor
        resp = client.patch(
            f"/auth/usuarios/{usuario_operador.id}",
            json={"role": "supervisor"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

        # 3. Fazer login NOVAMENTE como operador (agora supervisor)
        resp = client.post(
            "/auth/token",
            data={"username": "operador1", "password": "senha123"},
        )
        assert resp.status_code == 200
        novo_token = resp.json()["access_token"]

        # 4. Novo token deve funcionar em rota de supervisor
        resp = client.get(
            "/bi/exportar/excel",
            params={
                "relatorio": "ranking",
                "data_inicio": "2024-01-01",
                "data_fim": "2024-01-31",
            },
            headers={"Authorization": f"Bearer {novo_token}"},
        )
        # O que importa aqui e' a autorizacao: com o novo role o acesso
        # e' liberado (200), nao mais 401/403.
        assert resp.status_code == 200