from fastapi import APIRouter, Depends

from app.api.deps import get_empresa_do_usuario
from app.domain.enums import ModoOperacao, Segmento
from app.domain.models.empresa import Empresa
from app.domain.segmentos import modulos_da_empresa, rotulos_do_segmento
from app.schemas.empresa_schema import PerfilEmpresaResponse

router = APIRouter(prefix="/empresa", tags=["Empresa"])


@router.get("/perfil", response_model=PerfilEmpresaResponse)
def perfil(empresa: Empresa = Depends(get_empresa_do_usuario)):
    segmento = Segmento(empresa.segmento)
    modo = ModoOperacao(empresa.modo)
    return PerfilEmpresaResponse(
        nome=empresa.nome,
        segmento=segmento,
        modo=modo,
        modulos=sorted(modulos_da_empresa(segmento, modo)),
        rotulos=rotulos_do_segmento(segmento),
    )
