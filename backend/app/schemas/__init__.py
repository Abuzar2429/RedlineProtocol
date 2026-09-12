"""
Pydantic schemas for the Phase 1 API responses.
Simulation-specific schemas will be added in later phases.
"""
from pydantic import BaseModel


class RootResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
