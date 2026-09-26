from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.application.limpeza import limpar_registros_antigos
from app.domain.models.cache_status import CacheStatus
from app.domain.models.sync_job import SyncJob
from app.domain.models.tentativa_login import TentativaLogin
from app.domain.models.token_blacklist import TokenBlacklist
from tests.bancos import BANCOS, sessao_em_banco_limpo

AGORA = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
LOJA, OUTRA = 1, 2


@pytest.fixture(params=BANCOS)
def db(request):
    yield from sessao_em_banco_limpo(request.param, {LOJA: "loja", OUTRA: "outra"})


def _dias_atras(dias: int) -> datetime:
    return AGORA - timedelta(days=dias)


def _contar(db, modelo) -> int:
    return db.scalar(select(func.count()).select_from(modelo))


def test_remove_so_tokens_revogados_ja_expirados(db):
    db.add_all([
        TokenBlacklist(jti="expirado", user_id=1, expires_at=_dias_atras(1)),
        TokenBlacklist(jti="valido", user_id=1, expires_at=AGORA + timedelta(hours=1)),
    ])
    db.commit()

    limpar_registros_antigos(db, agora=AGORA)

    assert db.scalars(select(TokenBlacklist.jti)).all() == ["valido"]


def test_remove_tentativas_de_login_com_mais_de_30_dias(db):
    db.add_all([
        TentativaLogin(username="maria", attempted_at=_dias_atras(31)),
        TentativaLogin(username="maria", attempted_at=_dias_atras(29)),
    ])
    db.commit()

    resultado = limpar_registros_antigos(db, agora=AGORA)

    assert resultado.tentativas_login == 1
    assert _contar(db, TentativaLogin) == 1


def test_remove_sync_jobs_terminados_ha_mais_de_90_dias_e_preserva_em_andamento(db):
    db.add_all([
        SyncJob(empresa_id=LOJA, job_id="antigo", status="sucesso",
                started_at=_dias_atras(100), finished_at=_dias_atras(100)),
        SyncJob(empresa_id=LOJA, job_id="recente", status="sucesso",
                started_at=_dias_atras(10), finished_at=_dias_atras(10)),
        SyncJob(empresa_id=LOJA, job_id="travado", status="em_progresso",
                started_at=_dias_atras(100), finished_at=None),
    ])
    db.commit()

    limpar_registros_antigos(db, agora=AGORA)

    assert sorted(db.scalars(select(SyncJob.job_id)).all()) == ["recente", "travado"]


def test_cache_status_antigo_sai_mas_o_mais_recente_de_cada_empresa_fica(db):
    db.add_all([
        CacheStatus(empresa_id=LOJA, last_updated=_dias_atras(60), status="sucesso"),
        CacheStatus(empresa_id=LOJA, last_updated=_dias_atras(40), status="sucesso"),
        CacheStatus(empresa_id=LOJA, last_updated=_dias_atras(1), status="sucesso"),
        CacheStatus(empresa_id=OUTRA, last_updated=_dias_atras(90), status="erro"),
    ])
    db.commit()

    limpar_registros_antigos(db, agora=AGORA)

    restantes = db.execute(
        select(CacheStatus.empresa_id, CacheStatus.status).order_by(CacheStatus.empresa_id)
    ).all()
    assert restantes == [(LOJA, "sucesso"), (OUTRA, "erro")]


def test_status_invalido_e_rejeitado_pelo_banco(db):
    from sqlalchemy.exc import IntegrityError

    db.add(CacheStatus(empresa_id=LOJA, last_updated=AGORA, status="talvez"))
    with pytest.raises(IntegrityError):
        db.commit()
