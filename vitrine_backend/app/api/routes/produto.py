from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.deps import get_produto_repository, get_current_user, require_supervisor
from app.application.services.produto_service import ProdutoService
from app.schemas.produto_schema import ObservacaoNaoEncontrado, ProdutoPublicResponse, ProdutoResponse
from app.domain.value_objects.codigo import Codigo
from app.limiter import limiter
import logging

logger = logging.getLogger(__name__)
logger_nao_encontrado = logging.getLogger("app.nao_encontrado")

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def _buscar(codigo: str, repo, schema_class):
    try:
        codigo_valido = Codigo(codigo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Código inválido")

    produto = ProdutoService(repo).obter_por_codigo(codigo_valido.valor)

    if not produto:
        logger.warning("Produto não encontrado na API | codigo=%s", codigo)
        logger_nao_encontrado.info("Produto não encontrado | codigo=%s | origem=api", codigo)
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    response = schema_class.model_validate(produto)
    response.codigo_buscado = codigo_valido.valor
    return response


@router.get("/busca", response_model=list[ProdutoPublicResponse])
@limiter.limit("30/minute")
def buscar_produtos_por_nome(
    request: Request,
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
@limiter.limit("30/minute")
def listar_produtos(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    repo=Depends(get_produto_repository),
    _user=Depends(get_current_user),
):
    logger.info("Listando produtos | limit=%s offset=%s", limit, offset)
    service = ProdutoService(repo)
    return [ProdutoPublicResponse.model_validate(p) for p in service.listar_paginado(limit=limit, offset=offset)]


@router.get("/{codigo}", response_model=ProdutoPublicResponse)
@limiter.limit("60/minute")
def obter_produto_publico(
    request: Request,
    codigo: str,
    repo=Depends(get_produto_repository),
    _user=Depends(get_current_user),
):
    logger.info("Busca pública | codigo=%s", codigo)
    return _buscar(codigo, repo, ProdutoPublicResponse)


@router.get("/{codigo}/completo", response_model=ProdutoResponse)
@limiter.limit("30/minute")
def obter_produto_completo(
    request: Request,
    codigo: str,
    repo=Depends(get_produto_repository),
    _user=Depends(require_supervisor),
):
    logger.info("Busca completa | codigo=%s", codigo)
    return _buscar(codigo, repo, ProdutoResponse)

@router.post("/nao-encontrado", status_code=201)
@limiter.limit("20/minute")
def registrar_nao_encontrado(
    request: Request,
    body: ObservacaoNaoEncontrado,
    _user=Depends(get_current_user),
):
    logger.warning(
        "Produto não encontrado | codigo=%s | observacao=%s",
        body.codigo,
        body.observacao,
    )
    logger_nao_encontrado.info(
        "Produto não encontrado | codigo=%s | observacao=%s | origem=form",
        body.codigo,
        body.observacao,
    )
    return {"ok": True}