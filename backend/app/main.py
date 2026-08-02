import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.games import router as games_router


def create_app() -> FastAPI:
    # BEER_GAME_ENV=production の場合、/docs 等のスキーマ露出エンドポイントを無効化する
    is_production = os.getenv("BEER_GAME_ENV") == "production"
    app = FastAPI(
        title="Beer Game API",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(games_router)
    return app


app = create_app()
