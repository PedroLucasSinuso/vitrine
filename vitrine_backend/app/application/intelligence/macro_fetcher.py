"""
Fetches macro-economic indicators from Banco Central do Brasil (SGS API).

- Monthly indicators (IPCA, IGP-M, INPC): cached within current month
- Dynamic indicators (Selic): always live fetch
- No hardcoded fallbacks — if API fails, disponivel=False
"""

import json
from datetime import datetime, date
from sqlalchemy.orm import Session
import httpx

from app.core.models.macro import MacroIndicator
from app.domain.models.macro_cache import MacroCache

# BC SGS series catalog
INDICADORES_META = [
    {"chave": "selic_meta", "rotulo": "Selic (meta)", "serie": 432, "unidade": "%", "tipo": "dinamico"},
    {"chave": "selic_12m", "rotulo": "Selic acumulada (12m)", "serie": 4390, "unidade": "%", "tipo": "dinamico"},
    {"chave": "ipca_12m", "rotulo": "IPCA geral (12m)", "serie": 433, "unidade": "%", "tipo": "mensal"},
    {"chave": "ipca_alimentacao_12m", "rotulo": "IPCA Alimentação (12m)", "serie": 1635, "unidade": "%", "tipo": "mensal"},
    {"chave": "igpm_12m", "rotulo": "IGP-M (12m)", "serie": 189, "unidade": "%", "tipo": "mensal"},
    {"chave": "inpc_12m", "rotulo": "INPC (12m)", "serie": 188, "unidade": "%", "tipo": "mensal"},
    {"chave": "desemprego", "rotulo": "Taxa de desemprego", "serie": 24369, "unidade": "%", "tipo": "mensal"},
]


def _mes_ano_atual() -> str:
    """Returns current month as 'YYYY-MM'."""
    return date.today().strftime("%Y-%m")


def _formata_periodo(periodo_ref: str | None) -> str | None:
    """Converts '2026-04' to 'Abr/2026'."""
    if not periodo_ref:
        return None
    try:
        d = datetime.strptime(periodo_ref, "%Y-%m")
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        return f"{meses[d.month - 1]}/{d.year}"
    except ValueError:
        return periodo_ref


def _obter_ultimo_valor_bc(dados: list[dict]) -> tuple[float | None, str | None]:
    """Extract the most recent value and its period from BC SGS response.

    BC response format: [{"data": "01/04/2026", "valor": "7.8"}, ...]
    Returns (valor, periodo_ref) where periodo_ref is "2026-04".
    """
    if not dados:
        return None, None
    ultimo = dados[-1]  # BC returns chronological order
    try:
        valor = float(ultimo["valor"])
        data_str = ultimo["data"]  # "01/04/2026"
        dia, mes, ano = data_str.split("/")
        periodo_ref = f"{ano}-{mes}"
        return valor, periodo_ref
    except (KeyError, ValueError, TypeError):
        return None, None


async def _fetch_bc_serie(client: httpx.AsyncClient, serie: int) -> tuple[float | None, str | None]:
    """Fetch a single BC SGS series. Returns (valor, periodo_ref).
    Raises on failure to trigger the 'indisponivel' state.
    """
    today = date.today()
    # Fetch last 2 years to guarantee we get the latest 12-month accumulated value
    data_inicio = today.replace(year=today.year - 2).strftime("%d/%m/%Y")
    data_fim = today.strftime("%d/%m/%Y")
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
    response = await client.get(
        url,
        params={"formato": "json", "dataInicial": data_inicio, "dataFinal": data_fim},
        timeout=10.0,
    )
    response.raise_for_status()
    dados = response.json()
    return _obter_ultimo_valor_bc(dados)


def _obter_cache_mensal(db: Session, chave: str) -> MacroIndicator | None:
    """Get cached monthly indicator if still valid (same calendar month)."""
    row = db.query(MacroCache).filter(MacroCache.chave == chave).first()
    if not row:
        return None
    if row.mes_ano != _mes_ano_atual():
        return None  # Cache expired (different month)
    try:
        data = json.loads(row.valor_json)
        # consultado_em foi salvo como string (json.dumps(default=str)), converter de volta
        if isinstance(data.get("consultado_em"), str):
            data["consultado_em"] = datetime.fromisoformat(data["consultado_em"])
        return MacroIndicator(**data)
    except (json.JSONDecodeError, TypeError, KeyError, ValueError):
        return None


def _salvar_cache_mensal(db: Session, chave: str, indicador: MacroIndicator) -> None:
    """Save monthly indicator to cache."""
    existing = db.query(MacroCache).filter(MacroCache.chave == chave).first()
    if existing:
        existing.valor_json = json.dumps(indicador.__dict__, default=str)
        existing.consultado_em = indicador.consultado_em
        existing.mes_ano = _mes_ano_atual()
    else:
        db.add(MacroCache(
            chave=chave,
            valor_json=json.dumps(indicador.__dict__, default=str),
            consultado_em=indicador.consultado_em,
            mes_ano=_mes_ano_atual(),
        ))
    db.commit()


async def fetch_todos_indicadores(db: Session) -> dict[str, MacroIndicator]:
    """Fetch ALL indicators in parallel.

    - Monthly: checks cache first (valid if fetched this month). If cache miss, fetches live.
    - Dynamic: always fetches live.
    - If API fails: returns MacroIndicator(disponivel=False, mensagem=...).
    """
    resultados: dict[str, MacroIndicator] = {}
    agora = datetime.now()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for meta in INDICADORES_META:
            # Monthly check cache first
            if meta["tipo"] == "mensal":
                cached = _obter_cache_mensal(db, meta["chave"])
                if cached:
                    resultados[meta["chave"]] = cached
                    continue

            # Live fetch
            try:
                valor, periodo_ref = await _fetch_bc_serie(client, meta["serie"])
                if valor is not None:
                    indicador = MacroIndicator(
                        chave=meta["chave"],
                        rotulo=meta["rotulo"],
                        valor=valor,
                        disponivel=True,
                        unidade=meta["unidade"],
                        periodo_ref=periodo_ref,
                        periodo_ref_rotulo=_formata_periodo(periodo_ref),
                        consultado_em=agora,
                        mensagem=None,
                        tipo_fonte="bc_sgs",
                    )
                else:
                    # API returned data but couldn't parse
                    indicador = MacroIndicator(
                        chave=meta["chave"],
                        rotulo=meta["rotulo"],
                        valor=None,
                        disponivel=False,
                        unidade=meta["unidade"],
                        periodo_ref=None,
                        periodo_ref_rotulo=None,
                        consultado_em=agora,
                        mensagem=f"Banco Central (série {meta['serie']}) retornou dados inválidos.",
                        tipo_fonte="bc_sgs",
                    )
            except httpx.TimeoutException:
                indicador = MacroIndicator(
                    chave=meta["chave"],
                    rotulo=meta["rotulo"],
                    valor=None,
                    disponivel=False,
                    unidade=meta["unidade"],
                    periodo_ref=None,
                    periodo_ref_rotulo=None,
                    consultado_em=agora,
                    mensagem=f"Banco Central (série {meta['serie']}) — timeout de 10s.",
                    tipo_fonte="bc_sgs",
                )
            except httpx.HTTPStatusError as e:
                indicador = MacroIndicator(
                    chave=meta["chave"],
                    rotulo=meta["rotulo"],
                    valor=None,
                    disponivel=False,
                    unidade=meta["unidade"],
                    periodo_ref=None,
                    periodo_ref_rotulo=None,
                    consultado_em=agora,
                    mensagem=f"Banco Central (série {meta['serie']}) — HTTP {e.response.status_code}.",
                    tipo_fonte="bc_sgs",
                )
            except Exception as e:
                indicador = MacroIndicator(
                    chave=meta["chave"],
                    rotulo=meta["rotulo"],
                    valor=None,
                    disponivel=False,
                    unidade=meta["unidade"],
                    periodo_ref=None,
                    periodo_ref_rotulo=None,
                    consultado_em=agora,
                    mensagem=f"Banco Central (série {meta['serie']}) indisponível: {e}",
                    tipo_fonte="bc_sgs",
                )

            # Save monthly cache (even if failed — marks attempt for this month)
            if meta["tipo"] == "mensal":
                _salvar_cache_mensal(db, meta["chave"], indicador)

            resultados[meta["chave"]] = indicador

    return resultados
