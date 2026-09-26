import ast
from pathlib import Path

import pytest

PACOTE = Path(__file__).resolve().parents[1] / "vitrine_core"
PROIBIDOS = ("app", "fastapi", "sqlalchemy", "starlette", "psycopg", "psycopg2", "alembic")


def _modulos_importados(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8-sig"))
    nomes: set[str] = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(alias.name for alias in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            nomes.add(no.module)
    return nomes


@pytest.mark.parametrize("arquivo", sorted(PACOTE.rglob("*.py")), ids=lambda p: str(p.relative_to(PACOTE)))
def test_core_nao_depende_de_infraestrutura(arquivo: Path):
    violacoes = {
        nome for nome in _modulos_importados(arquivo)
        if nome.split(".")[0] in PROIBIDOS
    }
    assert not violacoes, f"{arquivo.name} importa {sorted(violacoes)}"


def test_modulos_do_core_importam_sem_o_backend():
    import importlib

    for arquivo in PACOTE.rglob("*.py"):
        relativo = arquivo.relative_to(PACOTE.parent).with_suffix("")
        importlib.import_module(".".join(relativo.parts).removesuffix(".__init__"))
