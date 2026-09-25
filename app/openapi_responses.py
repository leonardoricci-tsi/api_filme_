"""Blocos de resposta reutilizáveis pro Swagger.

Sem `responses=` explícito, o FastAPI só documenta o caminho de sucesso (e
o 422 automático de validação de body/query) — todo `HTTPException` que o
código levanta (401, 403, 404, 409, 502...) aparece como "Undocumented" no
Swagger UI até alguém clicar em "Try it out" e ver na marra. Esses helpers
existem só pra isso: descrever, com exemplo de payload, os erros que cada
rota já levanta de verdade — não duplicam lógica, só documentam o que já
existe (atividade "Documentando suas APIs com Swagger/OpenAPI").
"""


def _erro(descricao: str, detail: str) -> dict:
    return {"description": descricao, "content": {"application/json": {"example": {"detail": detail}}}}


RESP_401 = {401: _erro("Token ausente, inválido ou expirado", "Credenciais inválidas ou expiradas")}

RESP_403_ADMIN = {403: _erro("Autenticado, mas sem papel admin", "Acesso restrito a admins")}


def resp_403_papel(papel_minimo: str) -> dict:
    """`papel_minimo` é o menor papel que a rota aceita (ex.: "nerd",
    "stalker_do_tomhanks") — mesmo texto que `require_papel_minimo` devolve
    de verdade, não uma paráfrase."""
    return {
        403: _erro(
            f"Autenticado, mas com papel abaixo de '{papel_minimo}'",
            f"Ação exige papel '{papel_minimo}' ou superior",
        )
    }


RESP_404 = {404: _erro("Recurso não existe, ou não pertence ao usuário logado", "Recurso não encontrado")}

RESP_409_FAVORITO = {409: _erro("Esse filme já está nos favoritos do usuário", "Filme já favoritado")}

RESP_502_AUTH_SERVICE = {
    502: _erro(
        "auth-service fora do ar ou inalcançável pela rede interna",
        "Serviço de autenticação indisponível no momento",
    )
}

RESP_502_LOG_SERVICE = {
    502: _erro(
        "log-service fora do ar ou inalcançável pela rede interna",
        "Serviço de log indisponível no momento",
    )
}

RESP_502_TMDB = {
    502: _erro(
        "TMDB fora do ar, sem chave configurada, ou resposta inesperada — a "
        "mensagem exata varia conforme a falha",
        "Falha ao buscar movie_credits no TMDB: HTTP 500",
    )
}
