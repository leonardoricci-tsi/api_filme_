from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Usuario
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(dados: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    email_em_uso = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if email_em_uso is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
    )
    db.add(usuario)
    db.commit()

    token = create_access_token(usuario.id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def me(usuario_atual: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return usuario_atual


@router.post("/login", response_model=TokenOut)
def login(dados: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos"
    )

    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario is None or not verify_password(dados.senha, usuario.senha_hash):
        raise credenciais_invalidas

    token = create_access_token(usuario.id)
    return TokenOut(access_token=token)
