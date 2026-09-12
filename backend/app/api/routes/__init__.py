# API routes package
from app.api.routes.countries import router as countries_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.simulations import router as simulations_router

__all__ = ["countries_router", "scenarios_router", "simulations_router"]
