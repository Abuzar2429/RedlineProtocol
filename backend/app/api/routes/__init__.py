from app.api.routes.countries import router as countries_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.simulations import router as simulations_router
from app.api.routes.negotiations import router as negotiations_router
from app.api.routes.scoring import router as scoring_router
from app.api.routes.websocket import router as websocket_router
from app.api.routes.rag import router as rag_router
from app.api.routes.comparisons import router as comparisons_router
from app.api.routes.demo import router as demo_router

__all__ = [
    "countries_router",
    "scenarios_router",
    "simulations_router",
    "negotiations_router",
    "scoring_router",
    "websocket_router",
    "rag_router",
    "comparisons_router",
    "demo_router",
]

