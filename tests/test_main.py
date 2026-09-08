import sys
import os

# Add project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test that the root endpoint returns 200 and expected payload."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["project"] == "AI-Powered Research Paper Intelligence System"
    assert data["version"] == "1.0.0"
    assert data["documentation"] == "/docs"
    print("[PASS] Root endpoint '/' test passed successfully.")

def test_health_check_endpoint():
    """Test that the health endpoint returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "backend-api"
    assert data["uptime"] == "operational"
    print("[PASS] Health endpoint '/health' test passed successfully.")

def test_cors_headers():
    """Test that CORS headers are appropriately configured."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    print("[PASS] CORS configuration test passed successfully.")

if __name__ == "__main__":
    test_root_endpoint()
    test_health_check_endpoint()
    test_cors_headers()
    print("\n All backend tests passed successfully!")
