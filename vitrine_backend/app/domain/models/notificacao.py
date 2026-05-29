"""Modelo de Notificação Interna.

Usado para alertas pós-sync: margem negativa, erro de sync, encalhe severo, etc.
Cada notificação é consolidada (1 alerta = 1 linha, não 1 por produto).
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from app.infrastructure.db.database import Base


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False, index=True)
    """Tipos: margem_negativa, sync_erro, sync_lento, encalhe_severo, intelligence_pronto."""

    titulo = Column(String(200), nullable=False)
    mensagem = Column(Text, nullable=True)
    """Guidance/texto explicativo para o admin."""

    dados_json = Column(Text, nullable=True)
    """Metadados em JSON: contagem, link_relatorio, etc."""

    lida = Column(Boolean, default=False, index=True)
    resolvida = Column(Boolean, default=False, index=True)
    """resolvida=true quando o problema deixou de existir no próximo sync."""

    criada_em = Column(DateTime, default=func.now())
    lida_em = Column(DateTime, nullable=True)
    resolvida_em = Column(DateTime, nullable=True)

    def marcar_lida(self) -> None:
        self.lida = True
        self.lida_em = datetime.now()

    def marcar_resolvida(self) -> None:
        self.resolvida = True
        self.resolvida_em = datetime.now()
