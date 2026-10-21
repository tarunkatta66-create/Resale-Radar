"""
Pydantic schemas and validation for ResaleRadar API.
"""

from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, field_validator


class SmartphoneInput(BaseModel):
    device_type: Literal["smartphone"] = "smartphone"
    brand: Literal["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Google", "Vivo", "Oppo"]
    original_price: float = Field(..., ge=8000, le=150000, description="Original purchase price in INR (8,000 - 150,000)")
    age_months: int = Field(..., ge=1, le=60, description="Device age in months (1 - 60)")
    condition: Literal["Like New", "Good", "Fair", "Poor"]
    storage_gb: int = Field(..., description="Internal storage in GB")
    ram_gb: int = Field(..., description="RAM size in GB")
    battery_health_pct: int = Field(..., ge=60, le=100, description="Battery health percentage (60 - 100)")
    processor_tier: Literal["Entry", "Mid", "Flagship"]
    has_box_and_bill: int = Field(..., ge=0, le=1, description="1 if box & bill are present, else 0")

    @field_validator("storage_gb")
    @classmethod
    def validate_storage(cls, v: int) -> int:
        allowed = [64, 128, 256, 512]
        if v not in allowed:
            raise ValueError(f"Smartphone storage_gb must be one of {allowed}")
        return v

    @field_validator("ram_gb")
    @classmethod
    def validate_ram(cls, v: int) -> int:
        allowed = [3, 4, 6, 8, 12, 16]
        if v not in allowed:
            raise ValueError(f"Smartphone ram_gb must be one of {allowed}")
        return v


class LaptopInput(BaseModel):
    device_type: Literal["laptop"] = "laptop"
    brand: Literal["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI"]
    original_price: float = Field(..., ge=25000, le=250000, description="Original purchase price in INR (25,000 - 250,000)")
    age_months: int = Field(..., ge=1, le=72, description="Device age in months (1 - 72)")
    condition: Literal["Like New", "Good", "Fair", "Poor"]
    storage_gb: int = Field(..., description="Storage in GB")
    storage_type: Literal["SSD", "HDD"]
    ram_gb: int = Field(..., description="RAM size in GB")
    cpu_tier: Literal["Core i3/Ryzen 3", "Core i5/Ryzen 5", "Core i7/Ryzen 7", "Apple M-series"]
    gpu_type: Literal["Integrated", "Dedicated"]
    screen_size_in: float = Field(..., ge=12.0, le=20.0, description="Screen size in inches")
    battery_health_pct: int = Field(..., ge=50, le=100, description="Battery health percentage (50 - 100)")

    @field_validator("storage_gb")
    @classmethod
    def validate_laptop_storage(cls, v: int) -> int:
        allowed = [256, 512, 1024, 2048]
        if v not in allowed:
            raise ValueError(f"Laptop storage_gb must be one of {allowed}")
        return v

    @field_validator("ram_gb")
    @classmethod
    def validate_laptop_ram(cls, v: int) -> int:
        allowed = [4, 8, 16, 32]
        if v not in allowed:
            raise ValueError(f"Laptop ram_gb must be one of {allowed}")
        return v

    @field_validator("screen_size_in")
    @classmethod
    def validate_screen(cls, v: float) -> float:
        allowed = [13.3, 14.0, 15.6, 16.0, 17.3]
        # Round to 1 decimal place to handle float precision issues
        rounded_v = round(v, 1)
        if rounded_v not in allowed:
            raise ValueError(f"Laptop screen_size_in must be one of {allowed}")
        return rounded_v


# Discriminated union request type
PredictRequest = Annotated[Union[SmartphoneInput, LaptopInput], Field(discriminator="device_type")]


class PerModelPredictions(BaseModel):
    linear: int
    tree: int
    forest: int


class PredictResponse(BaseModel):
    device_type: str
    estimated_price: int
    price_low: int
    price_high: int
    depreciation_pct: float
    per_model_predictions: PerModelPredictions
    top_factors: list[str]
    disclaimer: str


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
