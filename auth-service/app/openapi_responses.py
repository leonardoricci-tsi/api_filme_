"""Blocos de resposta reutilizáveis pro Swagger — mesmo princípio do
`app/openapi_responses.py` do catálogo: sem `responses=` explícito, todo
`HTTPException` que o código levanta fica "Undocumented" no Swagger UI até
alguém clicar em "Try it out" e descobrir na marra."""


def _erro(descricao: str, detail: str) -> dict:
    return {"description": descricao, "content": {"application/json": {"example": {"detail": detail}}}}


RESP_401 = {401: _erro("Token ausente, inválido ou expirado", "Credenciais inválidas ou expiradas")}

RESP_403_ADMIN = {403: _erro("Autenticado, mas sem papel admin", "Acesso restrito a admins")}
