from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.api.deps import get_db, get_empresa_do_usuario
from app.application.perfil import modulos_ativos
from app.domain.enums import ModoOperacao, Segmento
from app.domain.models.empresa import Empresa
from app.domain.segmentos import rotulos_do_segmento
from app.schemas.empresa_schema import PerfilEmpresaResponse

router = APIRouter(prefix="/empresa", tags=["Empresa"])


@router.get("/perfil", response_model=PerfilEmpresaResponse)
def perfil(empresa: Empresa = Depends(get_empresa_do_usuario), db: Session = Depends(get_db)):
    segmento = Segmento(empresa.segmento)
    modo = ModoOperacao(empresa.modo)
    return PerfilEmpresaResponse(
        nome=empresa.nome,
        segmento=segmento,
        modo=modo,
        modulos=sorted(modulos_ativos(db, empresa)),
        rotulos=rotulos_do_segmento(segmento),
    )
