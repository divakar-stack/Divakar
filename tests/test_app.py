import os
from decimal import Decimal
from pathlib import Path

TEST_DB = Path(__file__).parent / "test_pocketsmart.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient

from main import app
from database import Base, engine

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    client.cookies.clear()


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


def register_user(email="person@example.com"):
    return client.post("/register", data={"username": "Planner", "email": email, "password": "secure-pass-123"}, follow_redirects=False)


def test_startup_and_home_page():
    with TestClient(app) as test_client:
        assert test_client.get("/startup").json() == {"status": "ok", "gemini_configured": False, "fallback_available": True}
        response = test_client.get("/")
        assert response.status_code == 200
        assert "PocketSmart" in response.text


def test_register_login_session_and_logout():
    response = register_user()
    assert response.status_code == 303
    assert client.get("/session-info").json()["authenticated"] is True
    client.get("/logout")
    login = client.post("/login", data={"email": "person@example.com", "password": "secure-pass-123"}, follow_redirects=False)
    assert login.status_code == 303
    assert client.get("/dashboard").status_code == 200
    client.get("/logout")
    assert client.get("/session-info").json()["authenticated"] is False


def test_dashboard_and_history_require_authentication():
    assert client.get("/dashboard", follow_redirects=False).headers["location"] == "/login"
    assert client.get("/history", follow_redirects=False).headers["location"] == "/login"
    assert client.get("/history", headers={"accept": "application/json"}).status_code == 401
    assert client.get("/recommendations-details").status_code == 401


def test_home_plan_fallback_and_invalid_budget():
    response = client.post("/generate-home", data={"total_budget": "12000", "home_type": "Apartment", "room_count": "1",
        "room_details": "Bright living room", "style_preference": "Modern", "required_items": "Lights: 2\nSofa: 1"})
    assert response.status_code == 200
    assert "AI service unavailable" in response.text
    assert "Lights" in response.text and "Sofa" in response.text
    invalid = client.post("/generate-home", data={"total_budget": "0", "home_type": "Apartment", "room_count": "1",
        "room_details": "Bright room", "style_preference": "Modern", "required_items": "Lights: -1"})
    assert invalid.status_code == 422
    assert "greater than 0" in invalid.text or "Input should be greater than 0" in invalid.text


def test_party_plan_fallback_and_missing_fields():
    data = {"total_budget": "50000", "guest_count": "40", "event_type": "Birthday", "venue_preference": "Garden",
        "event_date": "2026-12-31", "food_preference": "Vegetarian", "decoration_preference": "Flowers", "entertainment_preference": "Music"}
    response = client.post("/generate-party", data=data)
    assert response.status_code == 200
    assert "AI service unavailable" in response.text
    assert "Catering" in response.text and "remaining" in response.text.lower()
    data.pop("food_preference")
    invalid = client.post("/generate-party", data=data)
    assert invalid.status_code == 422
    assert "Field required" in invalid.text


def test_jewelry_plan_fallback_and_invalid_image():
    data = {"budget": "8000", "occasion": "Wedding", "jewelry_type": "Earrings", "style_preference": "Classic",
        "preferred_material": "Any", "color_preference": "Gold", "outfit_description": "Blue silk outfit"}
    response = client.post("/generate-jewelry", data=data)
    assert response.status_code == 200
    assert "AI service unavailable" in response.text
    assert "Pearl drop earrings" in response.text
    invalid = client.post("/generate-jewelry", data=data, files={"outfit_image": ("photo.gif", b"GIF89a", "image/gif")})
    assert invalid.status_code == 422
    assert "Upload a JPG, JPEG, PNG, or WEBP image." in invalid.text
    oversized = b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024)
    invalid_size = client.post("/generate-jewelry", data=data, files={"outfit_image": ("photo.jpg", oversized, "image/jpeg")})
    assert invalid_size.status_code == 422
    assert "5 MB or smaller" in invalid_size.text


def test_authenticated_history_is_user_specific():
    register_user()
    client.post("/generate-home", data={"total_budget": "10000", "home_type": "Apartment", "room_count": "1",
        "room_details": "Living room", "style_preference": "Modern", "required_items": "Lights: 1"})
    history = client.get("/history")
    assert history.status_code == 200
    assert "home plan" in history.text.lower()
    assert client.get("/recommendations-details").json()["recommendations"][0]["planner_type"] == "home"
    client.get("/logout")
    register_user("other@example.com")
    assert client.get("/recommendations-details").json()["recommendations"] == []


def test_not_found_page():
    assert client.get("/this-route-does-not-exist").status_code == 404


def test_fallback_rejects_over_budget_gemini_response(monkeypatch):
    from services import gemini_service, recommendation_service

    monkeypatch.setattr(gemini_service, "generate_home_recommendations", lambda *_: {
        "summary": "Over budget", "recommendations": [], "total_estimated": "999999", "remaining_budget": "0"})
    data, ai_used = recommendation_service.generate_home_recommendations({"total_budget": Decimal("100"), "home_type": "Room",
        "room_count": 1, "room_details": "Small room", "style_preference": "Modern", "items": [{"name": "Lamp", "quantity": 1}]})
    assert ai_used is False
    assert data["total_estimated"] <= Decimal("100")


def test_jewelry_fallback_keeps_combined_total_within_small_budget():
    from services.mock_catalog import jewelry_recommendations

    data = jewelry_recommendations({"budget": Decimal("100"), "occasion": "Dinner", "jewelry_type": "Any",
        "style_preference": "Minimal", "preferred_material": "Any", "color_preference": "Any", "outfit_description": "Blue dress"})
    assert data["total_estimated"] <= Decimal("100")
    assert data["total_estimated"] == sum((row["estimated_total"] for row in data["recommendations"]), Decimal(0))

