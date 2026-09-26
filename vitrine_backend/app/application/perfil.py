from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import ModoOperacao, Segmento
from app.domain.models.empresa import Empresa
from app.domain.models.importacao import Dataset
from app.domain.segmentos import modulos_da_empresa


def tipos_de_dataset(db: Session, empresa_id: int) -> set[str]:
    return set(db.scalars(select(Dataset.tipo).where(Dataset.empresa_id == empresa_id).distinct()))


def modulos_ativos(db: Session, empresa: Empresa) -> frozenset[str]:
    segmento, modo = Segmento(empresa.segmento), ModoOperacao(empresa.modo)
    tipos = tipos_de_dataset(db, empresa.id) if modo == ModoOperacao.UPLOAD else ()
    return modulos_da_empresa(segmento, modo, tipos)
