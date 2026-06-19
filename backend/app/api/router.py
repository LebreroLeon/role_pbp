from fastapi import APIRouter

from app.api.routes import auth, campaigns_mgmt, character_sheets, documents, entities, health, master, ooc, scenes, system_manuals, ws

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(campaigns_mgmt.router)
api_router.include_router(ooc.router)
api_router.include_router(character_sheets.router)
api_router.include_router(scenes.router)
api_router.include_router(master.router)
api_router.include_router(entities.router)
api_router.include_router(documents.router)
api_router.include_router(system_manuals.router)
api_router.include_router(ws.router)
