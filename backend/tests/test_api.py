import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import Base, get_db
from app.config import settings

# Тестовая БД в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Создаём таблицы
Base.metadata.create_all(bind=engine)

client = TestClient(app)

API_KEY = "antifraud_dev_key_2024"
HEADERS = {"X-API-Key": API_KEY}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "healthy" in response.json()["status"]


def test_check_endpoint():
    payload = {
        "email": "test@yopmail.com",
        "bin": "411111",
        "user_agent": "Mozilla/5.0",
        "ip": "8.8.8.8",
        "timezone": "Europe/London",
        "language": "en-US",
        "session_duration_ms": 1500,
        "typing_speed_ms_avg": 30,
        "mouse_moves_count": 0,
        "first_click_delay_ms": 100,
        "device_info": {"platform": "Linux"}
    }
    
    response = client.post("/api/check", json=payload, headers=HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert "risk_score" in data
    assert "fraud_flags" in data
    assert "recommendation" in data
    assert "check_id" in data
    assert data["risk_score"] > 0  # Должен быть высокий риск из-за временного email


def test_check_without_api_key():
    payload = {"email": "test@gmail.com", "ip": "8.8.8.8"}
    response = client.post("/api/check", json=payload)
    assert response.status_code == 401


def test_checks_list():
    response = client.get("/api/checks", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_blacklist_operations():
    # Добавляем IP в blacklist
    response = client.post("/api/blacklist", json={"ip": "1.2.3.4"}, headers=HEADERS)
    assert response.status_code == 200
    
    # Проверяем список blacklist
    response = client.get("/api/blacklist", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(entry["ip"] == "1.2.3.4" for entry in data)
