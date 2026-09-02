import base64
import io
import random
import time

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from PIL import Image

from app.auth.dependencies import UsuarioAutenticado, require_papel_minimo
from app.config import get_settings
from app.schemas.quiz import QuizPixeladoOut, QuizRespostaIn, QuizRespostaOut
from app.services.tmdb import TMDBError, get_tom_hanks_movies

router = APIRouter(prefix="/quiz", tags=["quiz"])

# Quão pequeno o pôster fica antes de ser ampliado de volta — quanto menor,
# mais "blocos" grandes e mais difícil de reconhecer o filme de cara.
TAMANHO_PIXELADO = 12
ROUND_TTL_SEGUNDOS = 300


def _pixelar(imagem_bytes: bytes) -> str:
    imagem = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    pequena = imagem.resize((TAMANHO_PIXELADO, TAMANHO_PIXELADO), Image.NEAREST)
    pixelada = pequena.resize(imagem.size, Image.NEAREST)

    buffer = io.BytesIO()
    pixelada.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _assinar_round(tmdb_movie_id: int) -> str:
    """O `round_id` carrega qual é o filme certo, assinado com o mesmo
    segredo do JWT — não precisa de nenhum estado guardado em memória ou
    banco (mesma lógica de token autocontido do login), e o cliente não
    consegue forjar nem ler qual é a resposta certa."""
    settings = get_settings()
    payload = {"tmdb_movie_id": tmdb_movie_id, "exp": time.time() + ROUND_TTL_SEGUNDOS}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _abrir_round(round_id: str) -> int:
    settings = get_settings()
    try:
        payload = jwt.decode(round_id, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Rodada inválida ou expirada"
        ) from erro
    return payload["tmdb_movie_id"]


@router.get("/pixelado", response_model=QuizPixeladoOut)
def novo_quiz_pixelado(
    _usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("stalker_do_tomhanks")),
) -> QuizPixeladoOut:
    """Só stalker_do_tomhanks: sorteia um filme, pixela o pôster de verdade
    (baixado ao vivo da TMDB, nunca persistido — mesma filosofia do resto
    do catálogo) e devolve 4 opções de título pro usuário adivinhar."""
    try:
        filmes = get_tom_hanks_movies()
    except TMDBError as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro

    com_poster = [f for f in filmes if f["poster_url"]]
    if len(com_poster) < 4:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TMDB não retornou pôsteres suficientes pro quiz",
        )

    correto = random.choice(com_poster)
    errados = random.sample([f for f in com_poster if f["tmdb_movie_id"] != correto["tmdb_movie_id"]], 3)
    opcoes = [correto["titulo"], *(f["titulo"] for f in errados)]
    random.shuffle(opcoes)

    try:
        resposta_imagem = httpx.get(correto["poster_url"], timeout=10.0)
        resposta_imagem.raise_for_status()
    except httpx.HTTPError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Falha ao baixar o pôster da TMDB"
        ) from erro

    return QuizPixeladoOut(
        round_id=_assinar_round(correto["tmdb_movie_id"]),
        opcoes=opcoes,
        imagem_base64=_pixelar(resposta_imagem.content),
    )


@router.post("/pixelado/resposta", response_model=QuizRespostaOut)
def responder_quiz_pixelado(
    dados: QuizRespostaIn,
    _usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("stalker_do_tomhanks")),
) -> QuizRespostaOut:
    """A checagem de acerto é sempre no servidor — o cliente nunca recebe
    a resposta certa antes de enviar a tentativa dele, só o `round_id`
    assinado (mesmo princípio de nunca confiar no cliente que motiva RBAC)."""
    tmdb_movie_id = _abrir_round(dados.round_id)

    try:
        filmes = get_tom_hanks_movies()
    except TMDBError as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro

    filme_correto = next((f for f in filmes if f["tmdb_movie_id"] == tmdb_movie_id), None)
    if filme_correto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filme da rodada não encontrado")

    titulo_certo = filme_correto["titulo"]
    correto = dados.resposta.strip().lower() == titulo_certo.strip().lower()
    return QuizRespostaOut(
        correto=correto,
        resposta_certa=titulo_certo,
        sinopse=filme_correto["sinopse"],
        poster_url=filme_correto["poster_url"],
        data_lancamento=filme_correto["data_lancamento"],
        nota=filme_correto["nota"],
    )
