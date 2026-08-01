"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import health, notes, papers, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(notes.router)
api_router.include_router(papers.router)
