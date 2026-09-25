from pydantic import BaseModel


class LogEventIn(BaseModel):
    usuario_id: int
    acao: str
    ip: str | None = None


class LogEventOut(BaseModel):
    usuario_id: int
    acao: str
    timestamp: str
    ip: str | None = None
