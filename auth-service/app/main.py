from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="Auth Service — Catálogo de Filmes")

app.include_router(auth.router)
