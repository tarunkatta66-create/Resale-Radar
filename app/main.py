"""
FastAPI application for ResaleRadar.
Serves prediction APIs, health checks, model metadata, and static frontend assets.
"""

import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.predictor import predictor
from app.schemas import (
    HealthResponse,
    LaptopInput,
    PredictRequest,
    PredictResponse,
    SmartphoneInput,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resale_radar")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ResaleRadar API",
    description="Intelligent resale valuation engine for used smartphones and laptops in India",
    version="1.0.0",
)

# Mount static folder
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Detailed validation error formatting
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        errors.append(f"{field}: {msg}")
    logger.warning("Validation error on %s: %s", request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors, "error_type": "ValidationError"},
    )


OPTIONS_DATA = {
    "smartphone": {
        "brands": ["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Google", "Vivo", "Oppo"],
        "conditions": ["Like New", "Good", "Fair", "Poor"],
        "storage_gb": [64, 128, 256, 512],
        "ram_gb": [3, 4, 6, 8, 12, 16],
        "processor_tiers": ["Entry", "Mid", "Flagship"],
        "has_box_and_bill": [
            {"label": "Yes (Original Box & Invoice Available)", "value": 1},
            {"label": "No (Handset Only)", "value": 0},
        ],
        "ranges": {
            "original_price": {"min": 8000, "max": 150000, "default": 45000, "step": 500, "label": "Original Purchase Price (₹)"},
            "age_months": {"min": 1, "max": 60, "default": 18, "step": 1, "label": "Device Age (Months)"},
            "battery_health_pct": {"min": 60, "max": 100, "default": 85, "step": 1, "label": "Battery Health (%)"},
        },
    },
    "laptop": {
        "brands": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI"],
        "conditions": ["Like New", "Good", "Fair", "Poor"],
        "storage_gb": [256, 512, 1024, 2048],
        "storage_types": ["SSD", "HDD"],
        "ram_gb": [4, 8, 16, 32],
        "cpu_tiers": ["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7", "Apple M-series"],
        "gpu_types": ["Integrated", "Dedicated"],
        "screen_sizes": [13.3, 14.0, 15.6, 16.0, 17.3],
        "ranges": {
            "original_price": {"min": 25000, "max": 250000, "default": 75000, "step": 1000, "label": "Original Purchase Price (₹)"},
            "age_months": {"min": 1, "max": 72, "default": 24, "step": 1, "label": "Device Age (Months)"},
            "battery_health_pct": {"min": 50, "max": 100, "default": 85, "step": 1, "label": "Battery Health (%)"},
        },
    },
}


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the single page application HTML."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            status_code=200,
            content={"message": "ResaleRadar API is running. static/index.html is being prepared."},
        )
    return FileResponse(index_file)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint confirming service and model readiness."""
    models_ok = (
        predictor.phone_model is not None
        and predictor.laptop_model is not None
        and predictor.phone_all is not None
        and predictor.laptop_all is not None
    )
    return {"status": "ok", "models_loaded": models_ok}


@app.get("/api/options")
async def get_options():
    """Provide schema options and numeric ranges for dynamic frontend form generation."""
    return OPTIONS_DATA


@app.get("/api/metrics")
async def get_metrics():
    """Return model performance metrics and feature importances."""
    metrics = predictor.get_metrics()
    if not metrics:
        raise HTTPException(status_code=500, detail="Metrics not available")
    return metrics


@app.post("/api/predict", response_model=PredictResponse)
async def predict_price(payload: PredictRequest):
    """Estimate resale price, confidence bounds, per-model predictions, and drivers."""
    data = payload.model_dump()
    device_type = data["device_type"]
    logger.info("Prediction requested for %s: %s", device_type, data["brand"])

    if device_type == "smartphone":
        result = predictor.predict_smartphone(data)
    elif device_type == "laptop":
        result = predictor.predict_laptop(data)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported device type: {device_type}")

    return result
