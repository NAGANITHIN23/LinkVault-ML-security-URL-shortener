from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models.link import Link
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_short_link():
    response = client.post(
        "/api/links/shorten",
        json={"original_url": "https://www.example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://www.example.com/"
    assert data["click_count"] == 0

def test_create_custom_short_link():
    response = client.post(
        "/api/links/shorten",
        json={
            "original_url": "https://www.example.com",
            "custom_code": "test123"
        }
    )
    assert response.status_code == 201
    assert response.json()["short_code"] == "test123"

def test_duplicate_custom_code():
    client.post(
        "/api/links/shorten",
        json={
            "original_url": "https://www.example.com",
            "custom_code": "duplicate"
        }
    )
    
    response = client.post(
        "/api/links/shorten",
        json={
            "original_url": "https://www.google.com",
            "custom_code": "duplicate"
        }
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_invalid_url():
    response = client.post(
        "/api/links/shorten",
        json={"original_url": "not-a-valid-url"}
    )
    assert response.status_code == 422

def test_get_link_info():
    create_response = client.post(
        "/api/links/shorten",
        json={"original_url": "https://www.example.com"}
    )
    short_code = create_response.json()["short_code"]
    
    response = client.get(f"/api/links/{short_code}")
    assert response.status_code == 200
    assert response.json()["short_code"] == short_code

def test_redirect():
    create_response = client.post(
        "/api/links/shorten",
        json={"original_url": "https://www.example.com"}
    )
    short_code = create_response.json()["short_code"]
    
    redirect_response = client.get(f"/{short_code}", follow_redirects=False)
    assert redirect_response.status_code == 307

def test_click_tracking():
    create_response = client.post(
        "/api/links/shorten",
        json={"original_url": "https://www.example.com"}
    )
    short_code = create_response.json()["short_code"]
    
    client.get(f"/{short_code}", follow_redirects=False)
    client.get(f"/{short_code}", follow_redirects=False)
    
    info_response = client.get(f"/api/links/{short_code}")
    assert info_response.json()["click_count"] == 2

def test_link_not_found():
    response = client.get("/nonexistent99999", follow_redirects=False)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Link not found"

def test_stats_summary():
    client.post("/api/links/shorten", json={"original_url": "https://www.google.com"})
    client.post("/api/links/shorten", json={"original_url": "https://www.youtube.com"})
    
    response = client.get("/api/links/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_links"] >= 2
    assert "top_links" in data

def test_expiring_link():
    response = client.post(
        "/api/links/shorten",
        json={
            "original_url": "https://www.example.com",
            "expires_in_days": 7
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["expires_at"] is not None

def test_get_all_links():
    client.post("/api/links/shorten", json={"original_url": "https://www.google.com"})
    client.post("/api/links/shorten", json={"original_url": "https://www.youtube.com"})
    
    response = client.get("/api/links/all")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2