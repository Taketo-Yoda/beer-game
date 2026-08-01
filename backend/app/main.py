from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.games import router as games_router


def create_app() -> FastAPI:
    app = FastAPI(title="Beer Game API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(games_router)
    return app


app = create_app()
