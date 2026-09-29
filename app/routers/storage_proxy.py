from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status

from app.config import get_settings

router = APIRouter(tags=["storage"])

_http_client: httpx.Client | None = None

# Cabeçalhos da resposta do Garage que valem a pena repassar pro navegador.
_CABECALHOS_REPASSADOS = ("content-type", "etag", "last-modified", "cache-control")


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(base_url=get_settings().s3_endpoint_url, timeout=10.0)
    return _http_client


@router.get("/" + get_settings().s3_bucket + "/{chave:path}", include_in_schema=False)
def repassar_para_o_garage(chave: str, request: Request) -> Response:
    """Repassa a URL pré-assinada da foto pro Garage, sem tocar na assinatura.

    O servidor da disciplina só expõe uma porta/domínio HTTPS (o do
    catálogo), então o Garage não pode ter porta pública — o navegador pede
    a foto aqui, no mesmo domínio, e o catálogo encaminha pela rede interna.
    Quem valida a assinatura e a expiração continua sendo o Garage: o
    caminho e a query vão intactos, e o `Host` enviado é o mesmo que entrou
    na assinatura (o de `s3_public_url`). Sem assinatura válida, o Garage
    responde 403 (e 400 "Date is too old" se a URL já expirou), e essa
    recusa volta pro navegador como veio — o bucket segue privado.

    Não é um endpoint da API (fica fora do Swagger): é só um túnel pro
    object storage."""
    settings = get_settings()
    try:
        # Caminho e query crus, byte a byte como chegaram: decodificar e
        # recodificar os parâmetros X-Amz-* poderia mudar a string assinada.
        resposta = _get_http_client().get(
            f"/{settings.s3_bucket}/{chave}?{request.url.query}",
            headers={"Host": urlsplit(settings.s3_public_url).netloc},
        )
    except httpx.RequestError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Armazenamento de arquivos indisponível no momento",
        ) from erro

    cabecalhos = {k: v for k, v in resposta.headers.items() if k.lower() in _CABECALHOS_REPASSADOS}
    return Response(content=resposta.content, status_code=resposta.status_code, headers=cabecalhos)
