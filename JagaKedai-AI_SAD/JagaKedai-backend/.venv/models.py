from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class DayType(str, Enum):
    weekday = "weekday"
    weekend = "weekend"


class DemandLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


# ─── INPUT ────────────────────────────────────────────────────────────────────

class ProductInput(BaseModel):
    # Basic product data
    product_name: str = Field(..., description="Name of the product")

    # Sales & stock
    units_sold_last_7_days: int = Field(..., ge=0, description="Units sold in last 7 days")
    current_stock: int = Field(..., ge=0, description="Units currently in stock")

    # Pricing
    cost_price: float = Field(..., gt=0, description="Cost price in RM")
    selling_price: float = Field(..., gt=0, description="Selling price in RM")
    competitor_price: float = Field(..., gt=0, description="Competitor price in RM")

    # Context
    local_event: Optional[str] = Field(default="none", description="Local event e.g. Hari Raya")
    day_type: DayType = Field(default=DayType.weekday, description="weekday or weekend")
    owner_note: Optional[str] = Field(default="", description="Extra context from the owner")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_name": "Teh Ais",
                    "units_sold_last_7_days": 120,
                    "current_stock": 40,
                    "cost_price": 0.80,
                    "selling_price": 2.50,
                    "competitor_price": 2.40,
                    "local_event": "Hari Raya",
                    "day_type": "weekend",
                    "owner_note": "Open extended hours during festive week",
                }
            ]
        }
    }


# ─── OUTPUT ───────────────────────────────────────────────────────────────────

class AdvisorOutput(BaseModel):
    demand_forecast: DemandLevel
    price_recommendation: str
    stock_recommendation: str
    bundle_suggestion: Optional[str] = None
    reasoning: str
    impact_estimate: str


class AnalyzeResponse(BaseModel):
    success: bool
    product: str
    result: Optional[AdvisorOutput] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    glm_reachable: bool
    message: str
