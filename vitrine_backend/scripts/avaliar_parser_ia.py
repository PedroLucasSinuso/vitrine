import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.importacao import ia  # noqa: E402
from app.application.importacao.llm import fabrica  # noqa: E402
from app.application.importacao.aplicacao import aplicar  # noqa: E402
from app.application.importacao.extracao import extrair  # noqa: E402
from app.application.importacao.mapeamento import Mapeamento  # noqa: E402
from tests.importacao import layouts, relatorios  # noqa: E402


def _layouts():
    conhecidos = {layout.nome: layout for layout in layouts.todos()}
    conhecidos["linx-like"] = layouts.Layout(
        nome="linx-like",
        arquivo="relatorio.xlsx",
        conteudo=relatorios.vendedores_xlsx(),
        mapeamento=None,
        tem_total=True,
        vendedores_esperados=frozenset(n for n, *_ in relatorios.VENDEDORES + relatorios.VENDEDORES_NORTE),
        bruto_esperado=sum(
            (layouts.D(v[3].replace(".", "").replace(",", ".")) for v in relatorios.VENDEDORES + relatorios.VENDEDORES_NORTE),
            layouts.D(0),
        ),
    )
    return conhecidos


def _avaliar(layout) -> tuple[bool, str]:
    grade = extrair(layout.conteudo, layout.arquivo)
    try:
        sugestao = ia.sugerir_mapeamento(grade)
        resultado = aplicar(grade, Mapeamento(**sugestao.mapeamento))
    except Exception as erro:
        return False, f"{type(erro).__name__}: {erro}"
    nomes = {r["vendedor"] for r in resultado.registros}
    bruto = sum((r["faturamento_bruto"] for r in resultado.registros), layouts.D(0))
    problemas = []
    if nomes != set(layout.vendedores_esperados):
        problemas.append(f"vendedores {sorted(nomes)}")
    if bruto != layout.bruto_esperado:
        problemas.append(f"faturamento {bruto} != {layout.bruto_esperado}")
    if resultado.validacao.status == "divergente":
        problemas.append("totais divergentes")
    if resultado.erros:
        problemas.append("; ".join(resultado.erros))
    return not problemas, ", ".join(problemas) or f"ok ({resultado.validacao.status}, confiança {sugestao.confianca})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Mede quantos layouts sintéticos a IA mapeia corretamente (faz chamadas pagas).")
    parser.add_argument("--somente", nargs="*", help="nomes de layouts a avaliar")
    parser.add_argument("--rodadas", type=int, default=1, help="repetições por layout (a IA não é determinística)")
    args = parser.parse_args()

    if not ia.ia_configurada():
        sys.exit("Configure a IA (IA_PROVEDOR, IA_MODELO e IA_API_KEY/ANTHROPIC_API_KEY; IA_BASE_URL para OpenAI-compatível).")

    todos = _layouts()
    escolhidos = [todos[n] for n in (args.somente or todos)]
    print(f"{len(escolhidos) * args.rodadas} chamadas ao modelo {fabrica.modelo_efetivo()} (provedor {ia.settings.ia_provedor}).")
    acertos = total = 0
    for layout in escolhidos:
        for rodada in range(args.rodadas):
            ok, detalhe = _avaliar(layout)
            total += 1
            acertos += ok
            print(f"{'OK  ' if ok else 'FALHA'} {layout.nome} (rodada {rodada + 1}): {detalhe}")
    print(f"\nAcerto: {acertos}/{total} ({100 * acertos / total:.0f}%)")


if __name__ == "__main__":
    main()
