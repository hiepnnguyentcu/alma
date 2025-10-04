from fastapi import APIRouter
from app.api.v1.endpoints import leads
from app.authentication import routes as auth_routes

api_router = APIRouter()

api_router.include_router(auth_routes.router, prefix="/auth", tags=["authentication"])
api_router.include_router(leads.router, tags=["leads"])
