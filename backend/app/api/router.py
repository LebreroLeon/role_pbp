from fastapi import APIRouter

from app.api.routes import entities, health, master, scenes

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(scenes.router)
api_router.include_router(master.router)
api_router.include_router(entities.router)
