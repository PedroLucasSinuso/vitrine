"""Validação de chaves de configuração — isolado do config_service.py.

Define quais chaves são editáveis via API, quais são somente .env,
e quais são consideradas sensíveis (não expor valor real no GET).
"""

# ── Chaves que SOMENTE vêm do .env (ignoram cache e banco) ────────────
# Estas chaves nunca devem ser lidas do SQLite nem sobrescritas via UI.
# Proteção crítica contra escalada de privilégio via JWT.
CHAVES_SOMENTE_ENV: set[str] = {"jwt_secret"}

# ── Whitelist de chaves editáveis via API ─────────────────────────────
# Qualquer chave não listada aqui será rejeitada por set_many().
# Mantenha esta lista sincronizada com as abas da UI de Admin > Configurações.
CHAVES_EDITAVEIS: set[str] = {
    # Aba Geral
    "nome_estabelecimento",
    "logo_url",
    # Aba Geral — Endereço
    "endereco_rua",
    "endereco_numero",
    "endereco_complemento",
    "endereco_bairro",
    "endereco_cidade",
    "endereco_estado",
    "endereco_cep",
    # Aba ERP — campos individuais
    "erp_host",
    "erp_port",
    "erp_database",
    "erp_user",
    "erp_password",
    "cache_refresh_interval",
    # Aba WhatsApp
    "twilio_account_sid",
    "twilio_auth_token",
    "twilio_from_number",
    # Aba E-mail
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "email_from",
    # Aba Intelligence / Agendamentos
    "report_day",
    "report_time",
    "report_email_day",
    "report_email_time",
    "etl_interval_minutes",
    "relatorio_dias_retroativos",
    # Aba Sistema
    "anthropic_api_key",
    "openai_api_key",
    # Intelligence — grupos ignorados
    "ignored_groups",
    # Aba Metas
    "meta_faturamento_mensal",
}

# Chaves sensíveis — nunca retornar valor real no GET.
# Usa heurística por nome + lista explícita para segurança extra.
_CHAVES_SENSIVEIS_POR_PADRAO: set[str] = {
    "twilio_auth_token", "twilio_account_sid",
    "smtp_password", "anthropic_api_key", "openai_api_key",
    "erp_password",
}

# Expansão da lista de sensíveis com padrões baseados em nome
_CHAVES_SENSIVEIS_POR_PADRAO = _CHAVES_SENSIVEIS_POR_PADRAO | {
    "jwt_secret", "erp_postgres_url", "erp_password",
    "postgres_password", "twilio_auth_token", "twilio_account_sid",
    "smtp_password", "anthropic_api_key", "openai_api_key",
}

# Chaves que corresponderiam a padrões mas não são sensíveis (ex: logo_url)
_CHAVES_NAO_SENSIVEIS: set[str] = {"logo_url"}

_termos_sensiveis = {"password", "secret", "token", "api_key", "auth_token", "sid", "url"}


def is_sensitive(chave: str) -> bool:
    """Retorna True se a chave é considerada sensível (não expor valor real).

    Usa lista explícita de padrões em vez de regex com negative lookbehind
    para clareza e manutenibilidade.
    """
    chave_lower = chave.lower()
    if chave_lower in _CHAVES_NAO_SENSIVEIS:
        return False
    if chave_lower in _CHAVES_SENSIVEIS_POR_PADRAO:
        return True
    # Heurística por palavra-chave no nome
    for termo in _termos_sensiveis:
        if termo in chave_lower:
            return True
    return False


def is_only_env(chave: str) -> bool:
    """Retorna True se a chave só pode vir do .env."""
    return chave in CHAVES_SOMENTE_ENV


def is_editable(chave: str) -> bool:
    """Retorna True se a chave é editável via API."""
    if chave in CHAVES_SOMENTE_ENV:
        return False
    return chave in CHAVES_EDITAVEIS
