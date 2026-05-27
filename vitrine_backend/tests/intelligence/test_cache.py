"""Tests for intelligence cache module."""
import json
from datetime import datetime, timedelta
from app.domain.models.intelligence_cache import IntelligenceCache
from app.application.intelligence.cache import obter_cache, salvar_cache, limpar_expirados
from app.application.intelligence._utils import utcnow


class TestCache:
    def test_salvar_e_obter_cache(self, db_session):
        """Salva cache e recupera com sucesso."""
        dados = {"resumo_executivo": "teste", "insights": []}
        salvar_cache(db_session, dados, "deterministico")
        resultado = obter_cache(db_session)
        assert resultado is not None
        assert resultado["resumo_executivo"] == "teste"

    def test_cache_expirado_retorna_none(self, db_session):
        """Cache expirado não deve ser retornado."""
        expirado = IntelligenceCache(
            tenant_id="default",
            periodo_key="30d",
            resultado_json=json.dumps({"x": 1}),
            fonte="deterministico",
            gerado_em=utcnow() - timedelta(days=10),
            expira_em=utcnow() - timedelta(days=1),
        )
        db_session.add(expirado)
        db_session.commit()
        assert obter_cache(db_session) is None

    def test_cache_valido_retorna_dict(self, db_session):
        """Cache dentro do prazo deve ser retornado."""
        valido = IntelligenceCache(
            tenant_id="default",
            periodo_key="30d",
            resultado_json=json.dumps({"y": 2}),
            fonte="deterministico",
            gerado_em=utcnow(),
            expira_em=utcnow() + timedelta(days=6),
        )
        db_session.add(valido)
        db_session.commit()
        resultado = obter_cache(db_session)
        assert resultado is not None
        assert resultado["y"] == 2

    def test_salvar_substitui_cache_existente(self, db_session):
        """Merge deve substituir cache existente."""
        dados1 = {"resumo_executivo": "primeiro"}
        dados2 = {"resumo_executivo": "segundo"}
        salvar_cache(db_session, dados1, "deterministico")
        salvar_cache(db_session, dados2, "deterministico")
        resultado = obter_cache(db_session)
        assert resultado["resumo_executivo"] == "segundo"

    def test_limpar_expirados_remove_apenas_expirados(self, db_session):
        """Limpeza deve remover só expirados, manter válidos."""
        expirado = IntelligenceCache(
            tenant_id="default",
            periodo_key="30d",
            resultado_json="{}",
            fonte="teste",
            gerado_em=utcnow() - timedelta(days=10),
            expira_em=utcnow() - timedelta(days=1),
        )
        valido = IntelligenceCache(
            tenant_id="default2",
            periodo_key="30d",
            resultado_json="{}",
            fonte="teste",
            gerado_em=utcnow(),
            expira_em=utcnow() + timedelta(days=6),
        )
        db_session.add_all([expirado, valido])
        db_session.commit()
        removidos = limpar_expirados(db_session)
        assert removidos == 1
        assert db_session.query(IntelligenceCache).count() == 1

    def test_cache_sem_expira_em_retorna_none(self, db_session):
        """Cache sem data de expiração não deve ser retornado."""
        sem_expira = IntelligenceCache(
            tenant_id="default",
            periodo_key="30d",
            resultado_json=json.dumps({"z": 3}),
            fonte="teste",
            gerado_em=utcnow(),
            expira_em=None,
        )
        db_session.add(sem_expira)
        db_session.commit()
        assert obter_cache(db_session) is None

    def test_cache_vazio_retorna_none(self, db_session):
        """Nenhum cache salvo retorna None."""
        assert obter_cache(db_session) is None
