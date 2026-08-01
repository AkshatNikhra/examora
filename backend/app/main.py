"""Examora API application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.firebase import init_firebase
from app.core.schema_migrate import ensure_note_processing_columns, ensure_phase4_schema
from app import models  # noqa: F401 — register models on Base.metadata


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.ENVIRONMENT != "test":
        init_firebase()
    Base.metadata.create_all(bind=engine)
    ensure_note_processing_columns(engine)
    ensure_phase4_schema(engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
