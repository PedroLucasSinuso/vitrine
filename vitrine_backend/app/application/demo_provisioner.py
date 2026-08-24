"""Provisionamento e reset do tenant de demonstração.

Fica em ``application`` (e não em ``cli.py``) porque o reset precisa poder
ser chamado de dentro do processo — de um job agendado, por exemplo — e o
CLI encerra o processo com ``sys.exit`` nos casos de erro.
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.application.utils.security import hash_password
from app.domain.models.configuracao import Configuracao
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from app.infrastructure.db.database import Base

logger = logging.getLogger(__name__)

SLUG_DEMO = "demo"

# Usuários criados na demo — um por papel, para dar para experimentar as
# três visões da interface.
USUARIOS_DEMO = (
    ("demo", "Demonstração (Admin)", "admin"),
    ("demo.supervisor", "Demonstração (Supervisor)", "supervisor"),
    ("demo.operador", "Demonstração (Operador)", "operador"),
)

# Configurações do tenant. Nada de twilio_*/smtp_* de propósito: com
# credencial de envio configurada, o scheduler de notificações mandaria
# mensagem de verdade para os contatos fictícios da demo.
CONFIG_DEMO = {
    "erp_adapter": "demo",
    "nome_estabelecimento": "Mercado Vitrine",
    "meta_faturamento_mensal": "200000",
    "etl_interval_minutes": "1440",
    "endereco_cidade": "Belo Horizonte",
    "endereco_estado": "MG",
}


class DemoError(RuntimeError):
    """Falha ao provisionar ou resetar o tenant de demonstração."""


def _gravar_config(session: Session, empresa_id: int, valores: dict[str, str]) -> None:
    """Escreve configurações direto no model.

    Não passa por ``config_service.set_many`` porque ``erp_adapter`` não é
    uma chave editável pela API — e não deve ser: um admin de cliente real
    que a trocasse para "demo" veria dados sintéticos como se fossem seus,
    e o sync seguinte apagaria o catálogo verdadeiro.
    """
    for chave, valor in valores.items():
        existente = session.get(Configuracao, (empresa_id, chave))
        if existente:
            existente.valor = valor
        else:
            session.add(Configuracao(empresa_id=empresa_id, chave=chave, valor=valor))


def _criar_usuarios(session: Session, empresa_id: int, senha: str) -> None:
    for username, nome, role in USUARIOS_DEMO:
        em_uso = session.execute(
            select(Usuario).where(Usuario.username == username)
        ).scalar_one_or_none()
        if em_uso:
            raise DemoError(
                f"Já existe um usuário '{username}' (empresa_id={em_uso.empresa_id}). "
                "O username é único em toda a plataforma."
            )
        session.add(
            Usuario(
                username=username,
                nome_exibicao=nome,
                role=role,
                hashed_password=hash_password(senha),
                empresa_id=empresa_id,
            )
        )


def _buscar_empresa_demo(session: Session, slug: str) -> Empresa | None:
    return session.execute(
        select(Empresa).where(Empresa.slug == slug)
    ).scalar_one_or_none()


def _garantir_que_e_demo(session: Session, empresa: Empresa) -> None:
    """Recusa operar sobre um tenant que não seja de demonstração.

    Guarda-corpo do reset: sem isto, um slug digitado errado apagaria os
    dados de um cliente real.
    """
    config = session.get(Configuracao, (empresa.id, "erp_adapter"))
    if config is None or config.valor != "demo":
        raise DemoError(
            f"A empresa '{empresa.slug}' (id={empresa.id}) não é de demonstração "
            f"(erp_adapter={config.valor if config else 'não definido'!r}). "
            "Operação abortada."
        )


def _apagar_dados(session: Session, empresa_id: int) -> None:
    """Remove todo dado operacional da empresa, preservando a própria linha.

    O SQLite deste projeto não liga ``PRAGMA foreign_keys``, então os
    ``ondelete=CASCADE`` dos models não são honrados — os filhos precisam
    ser apagados na mão. A ordem vem de ``sorted_tables`` invertida
    (dependentes primeiro), o que mantém isto correto quando alguém criar
    uma tabela nova.
    """
    for tabela in reversed(Base.metadata.sorted_tables):
        if tabela.name == "empresas" or "empresa_id" not in tabela.c:
            continue
        session.execute(delete(tabela).where(tabela.c.empresa_id == empresa_id))


def _semear_historico(session: Session, empresa_id: int, meses: int = 18) -> None:
    """Cria pontos retroativos de histórico de preço.

    Sem isto o gráfico de evolução de preço nasce com um ponto só — o
    histórico normalmente se acumula a cada sincronização diária.
    """
    from app.adapters.demo.catalog import CATALOGO
    from app.adapters.demo.pricing import custo_no_dia, preco_no_dia
    from app.domain.models.historico_preco import HistoricoPreco

    hoje = date.today()
    for sku in CATALOGO:
        for m in range(meses, 0, -1):
            dia = hoje - timedelta(days=30 * m)
            preco = float(preco_no_dia(sku, dia))
            custo = float(custo_no_dia(sku, dia))
            markup = (preco - custo) / custo * 100 if custo else 0.0
            margem = (preco - custo) / preco * 100 if preco else 0.0
            session.add(
                HistoricoPreco(
                    empresa_id=empresa_id,
                    codigo_chamada=sku.internal_code,
                    preco_venda=preco,
                    preco_custo=custo,
                    markup=round(markup, 2),
                    margem=round(margem, 2),
                    data_coleta=datetime.combine(dia, datetime.min.time()),
                )
            )


def provisionar_demo(senha: str, slug: str = SLUG_DEMO) -> int:
    """Cria o tenant de demonstração e o deixa pronto para uso.

    Returns:
        O ``empresa_id`` criado.
    """
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession

    init_db()
    with SqliteSession() as session:
        if _buscar_empresa_demo(session, slug):
            raise DemoError(
                f"Já existe uma empresa com slug '{slug}'. Use resetar_demo() "
                "para devolvê-la ao estado inicial."
            )

        empresa = Empresa(nome="Vitrine Demo", slug=slug, status="ativa")
        session.add(empresa)
        session.flush()

        _gravar_config(session, empresa.id, CONFIG_DEMO)
        _criar_usuarios(session, empresa.id, senha)
        session.commit()
        empresa_id = empresa.id

    _popular(empresa_id)
    logger.info("Tenant de demonstração provisionado | empresa_id=%s", empresa_id)
    return empresa_id


def _popular(empresa_id: int) -> None:
    """Roda o sync e semeia o que não vem do adapter."""
    from app.application.erp_factory import run_sync_common
    from app.infrastructure.db.session import SqliteSession

    with SqliteSession() as session:
        # As telas de produto, tabela de preços e inventário leem do SQLite,
        # não do adapter — sem este sync elas ficam vazias mesmo com o BI
        # cheio.
        run_sync_common(session, empresa_id, pool_size=1)
        _semear_historico(session, empresa_id)
        session.commit()


def resetar_demo(slug: str = SLUG_DEMO) -> int:
    """Devolve o tenant de demonstração ao estado inicial.

    Existe porque o visitante pode mexer à vontade (criar inventário,
    editar configuração). Preserva a linha da empresa para que o
    ``empresa_id`` continue o mesmo — caches e jobs do scheduler são
    chaveados por ele.
    """
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession

    init_db()
    with SqliteSession() as session:
        empresa = _buscar_empresa_demo(session, slug)
        if empresa is None:
            raise DemoError(f"Não existe empresa com slug '{slug}'.")
        _garantir_que_e_demo(session, empresa)
        empresa_id = empresa.id

        _apagar_dados(session, empresa_id)
        _gravar_config(session, empresa_id, CONFIG_DEMO)
        _criar_usuarios(session, empresa_id, senha_padrao())
        session.commit()

    _popular(empresa_id)

    # Sem isto o processo continuaria servindo a fonte de dados antiga: o
    # cache de adapters não tem expiração.
    from app.api.deps import limpar_cache_adapters
    from app.application.config_cache import invalidate_cache

    limpar_cache_adapters(empresa_id)
    invalidate_cache()

    logger.info("Tenant de demonstração resetado | empresa_id=%s", empresa_id)
    return empresa_id


def senha_padrao() -> str:
    """Senha dos usuários da demo — pública por definição."""
    return "demo1234"
