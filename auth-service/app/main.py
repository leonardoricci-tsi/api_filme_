from fastapi import FastAPI

from app.routers import admin, auth, health, password_reset

app = FastAPI(title="Auth Service — Catálogo de Filmes")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(password_reset.router)
app.include_router(admin.router)
