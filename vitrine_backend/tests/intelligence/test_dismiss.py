"""Tests for intelligence dismiss module."""
from app.application.intelligence.dismiss import dismiss_insight, is_dismissed, list_dismissed


class TestDismiss:
    def test_dismiss_marca_como_ignorado(self, db_session):
        """Dismiss deve marcar hash como ignorado."""
        dismiss_insight(db_session, "hash_abc")
        assert is_dismissed(db_session, "hash_abc") is True

    def test_is_dismissed_sem_dismiss(self, db_session):
        """Hash não ignorado retorna False."""
        assert is_dismissed(db_session, "hash_xyz") is False

    def test_list_dismissed_vazio(self, db_session):
        """Nenhum dismiss retorna set vazio."""
        assert list_dismissed(db_session) == set()

    def test_list_dismissed_com_items(self, db_session):
        """Deve listar todos os hashes ignorados."""
        dismiss_insight(db_session, "hash_a")
        dismiss_insight(db_session, "hash_b")
        result = list_dismissed(db_session)
        assert result == {"hash_a", "hash_b"}

    def test_dismiss_duplicado_nao_quebra(self, db_session):
        """Dismiss do mesmo hash duas vezes não deve causar erro."""
        dismiss_insight(db_session, "hash_dup")
        dismiss_insight(db_session, "hash_dup")  # merge
        assert list_dismissed(db_session) == {"hash_dup"}

    def test_dismiss_tenant_diferente(self, db_session):
        """Dismiss em tenant diferente não afeta outro tenant."""
        dismiss_insight(db_session, "hash_a", tenant_id="tenant1")
        assert is_dismissed(db_session, "hash_a", tenant_id="tenant2") is False
        assert is_dismissed(db_session, "hash_a", tenant_id="tenant1") is True
