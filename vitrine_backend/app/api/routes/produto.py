from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_produto_repository, get_current_user, require_supervisor
from app.application.services.produto_service import ProdutoService
from app.schemas.produto_schema import ObservacaoNaoEncontrado, ProdutoPublicResponse, ProdutoResponse
from app.domain.value_objects.codigo import Codigo
import logging

logger = logging.getLogger(__name__)
logger_nao_encontrado = logging.getLogger("app.nao_encontrado")

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def _buscar(codigo: str, repo, schema_class):
    try:
        codigo_valido = Codigo(codigo)
    except ValueError:
        raise HTTPException(status_code=400, detail="CÃ³digo invÃ¡lido")

    produto = ProdutoService(repo).obter_por_codigo(codigo_valido.valor)

    if not produto:
        logger.warning("Produto nÃ£o encontrado na API | codigo=%s", codigo)
        logger_nao_encontrado.info("Produto nÃ£o encontrado | codigo=%s | origem=api", codigo)
        raise HTTPException(status_code=404, detail="Produto nÃ£o encontrado")

    response = schema_class.model_validate(produto)
    response.codigo_buscado = codigo_valido.valor
    return response


@router.get("/busca", response_model=list[ProdutoPublicResponse])
def buscar_produtos_por_nome(
    nome: str,
    limit: int = 20,
    offset: int = 0,
    repo=Depends(get_produto_repository),
    _user=Depends(get_current_user),
):
    logger.info("Busca por nome | nome=%s limit=%s offset=%s", nome, limit, offset)
    service = ProdutoService(repo)
    return [ProdutoPublicResponse.model_validate(p) for p in service.buscar_por_nome(nome, limit=limit, offset=offset)]


@router.get("/", response_model=list[ProdutoPublicResponse])
def listar_produtos(
    limit: int = 50,
    offset: int = 0,
    repo=Depends(get_produto_repository),
    _user=Depends(get_current_user),
):
    logger.info("Listando produtos | limit=%s offset=%s", limit, offset)
    service = ProdutoService(repo)
    return [ProdutoPublicResponse.model_validate(p) for p in service.listar_paginado(limit=limit, offset=offset)]


@router.get("/{codigo}", response_model=ProdutoPublicResponse)
def obter_produto_publico(
    codigo: str,
    repo=Depends(get_produto_repository),
    _user=Depends(get_current_user),
):
    logger.info("Busca pÃºblica | codigo=%s", codigo)
    return _buscar(codigo, repo, ProdutoPublicResponse)


@router.get("/{codigo}/completo", response_model=ProdutoResponse)
def obter_produto_completo(
    codigo: str,
    repo=Depends(get_produto_repository),
    _user=Depends(require_supervisor),
):
    logger.info("Busca completa | codigo=%s", codigo)
    return _buscar(codigo, repo, ProdutoResponse)

@router.post("/nao-encontrado", status_code=201)
def registrar_nao_encontrado(
    body: ObservacaoNaoEncontrado,
    _user=Depends(get_current_user),
):
    logger.warning(
        "Produto nÃ£o encontrado | codigo=%s | observacao=%s",
        body.codigo,
        body.observacao,
    )
    logger_nao_encontrado.info(
        "Produto nÃ£o encontrado | codigo=%s | observacao=%s | origem=form",
        body.codigo,
        body.observacao,
    )
    return {"ok": True}