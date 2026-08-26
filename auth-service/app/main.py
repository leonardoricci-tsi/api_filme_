from fastapi import FastAPI

from app.routers import auth, password_reset

app = FastAPI(title="Auth Service — Catálogo de Filmes")

app.include_router(auth.router)
app.include_router(password_reset.router)
