from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth, comments, favorites, movies

app = FastAPI(title="Catálogo de Filmes — Tom Hanks")

app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(favorites.router)
app.include_router(comments.router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
