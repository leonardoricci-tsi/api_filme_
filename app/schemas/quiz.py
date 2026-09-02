from pydantic import BaseModel


class QuizPixeladoOut(BaseModel):
    round_id: str
    opcoes: list[str]
    imagem_base64: str


class QuizRespostaIn(BaseModel):
    round_id: str
    resposta: str


class QuizRespostaOut(BaseModel):
    correto: bool
    resposta_certa: str
    sinopse: str
    poster_url: str | None
    data_lancamento: str | None
    nota: float | None
