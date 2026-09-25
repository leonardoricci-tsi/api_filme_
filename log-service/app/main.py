from fastapi import FastAPI

from app.routers import logs

app = FastAPI(title="Log Service — Auditoria")

app.include_router(logs.router)
