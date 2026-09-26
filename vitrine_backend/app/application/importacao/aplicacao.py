from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal

from app.application.importacao import normalizacao as norm
from app.application.importacao.extracao import Celula, Grade
from app.application.importacao.mapeamento import CAMPOS, TIPOS_POR_PERIODO, Mapeamento
from vitrine_core.datasets.tipos import Operacao

TOLERANCIA = {"numero": Decimal("0.05"), "inteiro": Decimal("0")}


@dataclass(frozen=True)
class DiferencaTotal:
    campo: str
    calculado: Decimal
    informado: Decimal


@dataclass(frozen=True)
class Validacao:
    status: Literal["conferido", "divergente", "sem_total"]
    diferencas: list[DiferencaTotal] = field(default_factory=list)
    campos_conferidos: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LinhaDescartada:
    indice: int
    motivo: str


@dataclass
class ResultadoAplicacao:
    registros: list[dict]
    descartadas: list[LinhaDescartada]
    validacao: Validacao
    periodo: tuple[date, date] | None
    erros: list[str]

    @property
    def confirmavel(self) -> bool:
        return not self.erros and bool(self.registros) and self.validacao.status != "divergente"


def _vazia(linha: list[Celula]) -> bool:
    return all(c is None or (isinstance(c, str) and not c.strip()) for c in linha)


def _primeiro_texto(linha: list[Celula]) -> str:
    return next((norm.normalizar_texto(c) for c in linha if isinstance(c, str) and c.strip()), "")


def _eh_linha_ignorada(linha: list[Celula], marcadores: list[str]) -> bool:
    primeiro = _primeiro_texto(linha)
    return any(primeiro.startswith(norm.normalizar_texto(m)) for m in marcadores)


def _operacao(valor: Celula) -> Operacao:
    texto = norm.normalizar_texto(valor)
    return Operacao.TROCA if "troc" in texto or "devol" in texto else Operacao.VENDA


def _converter(valor: Celula, tipo: str, mapeamento: Mapeamento):
    if tipo == "texto":
        return norm.texto(valor)
    if tipo == "numero":
        return norm.numero(valor, mapeamento.separador_decimal)
    if tipo == "inteiro":
        return norm.inteiro(valor, mapeamento.separador_decimal)
    if tipo == "data":
        return norm.data(valor, mapeamento.formato_data)
    if tipo == "hora":
        return norm.hora(valor)
    return _operacao(valor)


def detectar_periodo(grade: Grade, ate_linha: int) -> tuple[date, date] | None:
    datas = [d for linha in grade.linhas[:ate_linha] for c in linha for d in norm.datas_no_texto(c)]
    return (min(datas), max(datas)) if datas else None


def _linha_de_total(totais: list[list[Celula]]) -> list[Celula] | list[list[Celula]] | None:
    if not totais:
        return None
    geral = [t for t in totais if "geral" in _primeiro_texto(t)]
    return [geral[-1]] if geral else totais


def _validar(registros: list[dict], totais: list[list[Celula]], mapeamento: Mapeamento) -> Validacao:
    candidatas = _linha_de_total(totais)
    if not candidatas:
        return Validacao(status="sem_total")
    campos = CAMPOS[mapeamento.tipo]
    diferencas, conferidos = [], []
    for coluna in mapeamento.colunas:
        campo = campos[coluna.campo]
        if not campo.somavel:
            continue
        valores = [
            _converter(linha[coluna.indice], campo.tipo, mapeamento)
            for linha in candidatas
            if coluna.indice < len(linha)
        ]
        valores = [v for v in valores if v is not None]
        if not valores:
            continue
        informado = Decimal(sum(valores))
        calculado = Decimal(sum((r[coluna.campo] or 0) for r in registros))
        conferidos.append(coluna.campo)
        if abs(calculado - informado) > TOLERANCIA[campo.tipo]:
            diferencas.append(DiferencaTotal(coluna.campo, calculado, informado))
    if not conferidos:
        return Validacao(status="sem_total")
    return Validacao(status="divergente" if diferencas else "conferido", diferencas=diferencas, campos_conferidos=conferidos)


def aplicar(grade: Grade, mapeamento: Mapeamento) -> ResultadoAplicacao:
    campos = CAMPOS[mapeamento.tipo]
    registros: list[dict] = []
    descartadas: list[LinhaDescartada] = []
    totais: list[list[Celula]] = []
    erros: list[str] = []

    if mapeamento.linha_cabecalho >= len(grade.linhas):
        erros.append("A linha de cabeçalho indicada não existe no arquivo.")
        return ResultadoAplicacao([], [], Validacao(status="sem_total"), None, erros)

    for indice in range(mapeamento.linha_cabecalho + 1, len(grade.linhas)):
        linha = grade.linhas[indice]
        if _vazia(linha):
            continue
        if _eh_linha_ignorada(linha, mapeamento.ignorar_linhas_com):
            if "total" in _primeiro_texto(linha):
                totais.append(linha)
            continue

        registro: dict = {}
        problemas: list[str] = []
        for coluna in mapeamento.colunas:
            campo = campos[coluna.campo]
            bruto = linha[coluna.indice] if coluna.indice < len(linha) else None
            valor = _converter(bruto, campo.tipo, mapeamento)
            if valor is None and campo.obrigatorio:
                problemas.append(f"{campo.rotulo} vazio ou inválido")
            registro[coluna.campo] = valor
        if problemas:
            descartadas.append(LinhaDescartada(indice, "; ".join(problemas)))
            continue
        registros.append(registro)

    periodo = None
    if mapeamento.tipo in TIPOS_POR_PERIODO:
        if mapeamento.periodo:
            periodo = (mapeamento.periodo.inicio, mapeamento.periodo.fim)
        else:
            periodo = detectar_periodo(grade, mapeamento.linha_cabecalho)
        if periodo is None:
            erros.append("Período não encontrado no arquivo: informe o início e o fim.")
    elif registros:
        datas = [r["data"] for r in registros]
        periodo = (min(datas), max(datas))

    if not registros and not erros:
        erros.append("Nenhuma linha válida com esse mapeamento.")

    return ResultadoAplicacao(
        registros=registros,
        descartadas=descartadas,
        validacao=_validar(registros, totais, mapeamento),
        periodo=periodo,
        erros=erros,
    )
