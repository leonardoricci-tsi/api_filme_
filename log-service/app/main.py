from fastapi import FastAPI

from app.routers import health, logs

app = FastAPI(title="Log Service — Auditoria")

app.include_router(health.router)
app.include_router(logs.router)
