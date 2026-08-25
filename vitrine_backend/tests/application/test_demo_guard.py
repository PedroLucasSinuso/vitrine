"""Cooldown e agendamento do reset da demonstração."""

import pytest

from app.application import demo_guard
from app.application.demo_provisioner import DemoError


@pytest.fixture(autouse=True)
def relogio_limpo(monkeypatch):
    """Zera o relógio do módulo entre testes — ele é estado de processo."""
    monkeypatch.setattr(demo_guard, "_ultimo_reset", None)


@pytest.fixture
def resets(monkeypatch):
    chamadas = []
    monkeypatch.setattr(demo_guard, "resetar_demo", lambda slug: chamadas.append(slug))
    return chamadas


def test_primeira_entrada_sempre_reseta(resets):
    assert demo_guard.resetar_se_necessario() is True
    assert len(resets) == 1


def test_entrada_seguida_nao_reseta_de_novo(resets):
    demo_guard.resetar_se_necessario()

    assert demo_guard.resetar_se_necessario() is False
    assert len(resets) == 1, "dois visitantes juntos derrubariam a sessão um do outro"


def test_reseta_de_novo_passado_o_cooldown(resets, monkeypatch):
    demo_guard.resetar_se_necessario()
    monkeypatch.setattr(demo_guard, "_cooldown_segundos", lambda: 0)

    assert demo_guard.resetar_se_necessario() is True
    assert len(resets) == 2


def test_falha_no_reset_nao_impede_a_entrada(monkeypatch):
    def explode(slug):
        raise DemoError("banco travado")

    monkeypatch.setattr(demo_guard, "resetar_demo", explode)

    # Não levanta: pior o visitante ver dado sujo do que uma tela de erro.
    assert demo_guard.resetar_se_necessario() is False


def test_falha_no_reset_ainda_segura_o_cooldown(monkeypatch):
    """Um reset que falha não pode virar reset a cada request.

    Sem isto, um banco em erro faria toda entrada tentar de novo — e cada
    tentativa é um ciclo de apagar/repovoar em cima de um banco doente.
    """
    tentativas = []

    def explode(slug):
        tentativas.append(slug)
        raise DemoError("banco travado")

    monkeypatch.setattr(demo_guard, "resetar_demo", explode)

    demo_guard.resetar_se_necessario()
    demo_guard.resetar_se_necessario()

    assert len(tentativas) == 1


class SchedulerFalso:
    def __init__(self):
        self.jobs = []

    def add_job(self, func, **kwargs):
        self.jobs.append(kwargs)


def test_agenda_o_job_periodico(monkeypatch):
    monkeypatch.setattr(
        demo_guard.settings, "demo_reset_interval_minutes", 180, raising=False
    )
    sched = SchedulerFalso()

    demo_guard.agendar_reset_periodico(sched)

    assert len(sched.jobs) == 1
    assert sched.jobs[0]["minutes"] == 180
    assert sched.jobs[0]["id"] == demo_guard.JOB_ID_RESET_DEMO


def test_intervalo_zero_desliga_so_a_camada_periodica(monkeypatch):
    monkeypatch.setattr(
        demo_guard.settings, "demo_reset_interval_minutes", 0, raising=False
    )
    sched = SchedulerFalso()

    demo_guard.agendar_reset_periodico(sched)

    assert sched.jobs == []
