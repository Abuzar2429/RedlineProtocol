"""
Phase 1 backend tests — verifies the two foundation endpoints.

Run with:
    cd backend
    pytest tests/ -v
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    """Async test client for the FastAPI app (no real DB needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_returns_200(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_root_response_body(client: AsyncClient):
    response = await client.get("/")
    body = response.json()
    assert "message" in body
    assert body["message"] == "AI Governance Crisis Simulator API"


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_body(client: AsyncClient):
    response = await client.get("/health")
    body = response.json()
    assert "status" in body
    assert body["status"] == "healthy"


@pytest.mark.asyncio
async def test_cors_headers_present(client: AsyncClient):
    """Verify CORS preflight is handled (Origin from allowed list)."""
    response = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORSMiddleware returns 200 for OPTIONS preflight
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
