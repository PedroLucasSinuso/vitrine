"""Tests for intelligence cost control module."""
from app.application.intelligence.cost_control import (
    pode_solicitar,
    registrar_chamada,
    chamadas_no_mes,
)


class TestCostControl:
    def test_pode_solicitar_sem_registros(self, db_session):
        """Sem registros de uso, deve permitir."""
        assert pode_solicitar(db_session) is True

    def test_pode_solicitar_dentro_do_limite(self, db_session):
        """Com 5 chamadas em limite de 10, deve permitir."""
        for _ in range(5):
            registrar_chamada(db_session)
        assert pode_solicitar(db_session, max_calls=10) is True

    def test_pode_solicitar_no_limite(self, db_session):
        """Exatamente 10 chamadas, deve negar."""
        for _ in range(10):
            registrar_chamada(db_session)
        assert pode_solicitar(db_session, max_calls=10) is False

    def test_pode_solicitar_acima_do_limite(self, db_session):
        """Mais de 10 chamadas, deve negar."""
        for _ in range(11):
            registrar_chamada(db_session)
        assert pode_solicitar(db_session, max_calls=10) is False

    def test_chamadas_no_mes_sem_registros(self, db_session):
        """Sem registros, retorna 0."""
        assert chamadas_no_mes(db_session) == 0

    def test_chamadas_no_mes_com_registros(self, db_session):
        """Deve retornar contagem correta."""
        for _ in range(3):
            registrar_chamada(db_session)
        assert chamadas_no_mes(db_session) == 3

    def test_registrar_chamada_incrementa(self, db_session):
        """Cada chamada incrementa contador."""
        registrar_chamada(db_session)
        assert chamadas_no_mes(db_session) == 1
        registrar_chamada(db_session)
        assert chamadas_no_mes(db_session) == 2

    def test_pode_solicitar_tenant_diferente(self, db_session):
        """Tenants diferentes têm buckets independentes."""
        registrar_chamada(db_session)  # tenant default
        assert pode_solicitar(db_session, tenant_id="outro_tenant", max_calls=1) is True
        assert pode_solicitar(db_session, max_calls=1) is False  # já usou 1

    def test_max_calls_0_sempre_nega(self, db_session):
        """max_calls=0 nunca permite chamada."""
        assert pode_solicitar(db_session, max_calls=0) is False
