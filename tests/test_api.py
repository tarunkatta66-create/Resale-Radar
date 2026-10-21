"""
API integration and validation tests for ResaleRadar.
Tests health, valid smartphone, valid laptop, invalid category, out-of-range inputs.
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["models_loaded"] is True


def test_options_endpoint():
    response = client.get("/api/options")
    assert response.status_code == 200
    data = response.json()
    assert "smartphone" in data
    assert "laptop" in data
    assert "Apple" in data["smartphone"]["brands"]
    assert "SSD" in data["laptop"]["storage_types"]


def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "smartphone" in data
    assert "laptop" in data
    assert "models" in data["smartphone"]
    assert "forest" in data["smartphone"]["models"]


def test_predict_valid_smartphone():
    payload = {
        "device_type": "smartphone",
        "brand": "Apple",
        "original_price": 79900,
        "age_months": 18,
        "condition": "Good",
        "storage_gb": 128,
        "ram_gb": 6,
        "battery_health_pct": 86,
        "processor_tier": "Mid",
        "has_box_and_bill": 1,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["device_type"] == "smartphone"
    assert data["estimated_price"] > 0
    assert data["price_low"] <= data["estimated_price"]
    assert data["price_high"] >= data["estimated_price"]
    assert 0.0 <= data["depreciation_pct"] <= 100.0
    assert "linear" in data["per_model_predictions"]
    assert "tree" in data["per_model_predictions"]
    assert "forest" in data["per_model_predictions"]
    assert len(data["top_factors"]) == 3
    assert len(data["disclaimer"]) > 10


def test_predict_valid_laptop():
    payload = {
        "device_type": "laptop",
        "brand": "Dell",
        "original_price": 85000,
        "age_months": 24,
        "condition": "Good",
        "storage_gb": 512,
        "storage_type": "SSD",
        "ram_gb": 16,
        "cpu_tier": "Core i5/Ryzen 5",
        "gpu_type": "Dedicated",
        "screen_size_in": 15.6,
        "battery_health_pct": 82,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["device_type"] == "laptop"
    assert data["estimated_price"] > 0
    assert data["price_low"] <= data["estimated_price"]
    assert data["price_high"] >= data["estimated_price"]
    assert len(data["top_factors"]) == 3


def test_predict_invalid_category_returns_422():
    payload = {
        "device_type": "smartphone",
        "brand": "UnknownBrandFake",
        "original_price": 40000,
        "age_months": 12,
        "condition": "Good",
        "storage_gb": 128,
        "ram_gb": 6,
        "battery_health_pct": 90,
        "processor_tier": "Mid",
        "has_box_and_bill": 1,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_predict_out_of_range_age_returns_422():
    payload = {
        "device_type": "smartphone",
        "brand": "Samsung",
        "original_price": 40000,
        "age_months": 999,  # Out of range (max 60)
        "condition": "Good",
        "storage_gb": 128,
        "ram_gb": 6,
        "battery_health_pct": 90,
        "processor_tier": "Mid",
        "has_box_and_bill": 1,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_predict_out_of_range_price_returns_422():
    payload = {
        "device_type": "laptop",
        "brand": "Dell",
        "original_price": 5000,  # Below min 25000
        "age_months": 12,
        "condition": "Good",
        "storage_gb": 512,
        "storage_type": "SSD",
        "ram_gb": 16,
        "cpu_tier": "Core i5/Ryzen 5",
        "gpu_type": "Dedicated",
        "screen_size_in": 15.6,
        "battery_health_pct": 85,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422
