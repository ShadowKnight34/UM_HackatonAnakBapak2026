from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ProductInput, AnalyzeResponse, HealthResponse
from glm_client import analyze_product, check_glm_health
from demo_data import get_demo, DEMO_SCENARIOS
from data_processor import calculate_metrics, generate_weekly_trend, calculate_restock_quantity

# ─── APP SETUP ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SME Smart Pricing & Inventory Advisor",
    description="AI-powered decision intelligence for Malaysian warung & retail owners, powered by Z.AI GLM.",
    version="1.0.0",
)

# Allow frontend (React/etc.) to call this backend locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "app": "SME Smart Pricing & Inventory Advisor",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Confirms the backend is alive and tests GLM connectivity.
    Call this first to verify your ILMU API key is working.
    """
    glm_ok, message = check_glm_health()
    return HealthResponse(
        status="ok" if glm_ok else "degraded",
        glm_reachable=glm_ok,
        message=message,
    )


@app.post("/api/analyze", response_model=AnalyzeResponse, tags=["Core"])
def analyze(product: ProductInput):
    """
    Main endpoint — send product data, receive AI-powered decisions.

    The GLM will return:
    - demand_forecast (high / medium / low)
    - price_recommendation
    - stock_recommendation
    - bundle_suggestion (optional)
    - reasoning
    - impact_estimate
    """
    try:
        result = analyze_product(product)
        return AnalyzeResponse(
            success=True,
            product=product.product_name,
            result=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"GLM response parsing failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GLM call failed: {str(e)}")


@app.post("/api/metrics", tags=["Core"])
def get_metrics(product: ProductInput):
    """
    Returns pre-calculated business metrics for dashboard display.
    No GLM call needed — instant math-based calculations.

    Returns:
    - daily_avg_sales, days_of_stock_left, stock_urgency
    - weekly_revenue, weekly_profit, margin_percent
    - pricing_position vs competitor
    - 7-day sales trend (for charts)
    - restock recommendation
    """
    metrics = calculate_metrics(product)
    trend = generate_weekly_trend(product)
    restock = calculate_restock_quantity(product)

    return {
        "product": product.product_name,
        "metrics": metrics,
        "weekly_trend": trend,
        "restock": restock,
    }


@app.get("/api/demo/{scenario}", response_model=AnalyzeResponse, tags=["Demo"])
def run_demo(scenario: str):
    """
    Fire one of the 3 pre-built demo scenarios by name.

    Scenarios:
    - **normal_day** — Nasi Lemak, steady weekday sales
    - **festive_season** — Teh Ais during Hari Raya (BEST for demo video)
    - **slow_moving** — Fries with excess stock, low demand
    """
    try:
        product = get_demo(scenario)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        result = analyze_product(product)
        return AnalyzeResponse(
            success=True,
            product=product.product_name,
            result=result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GLM call failed: {str(e)}")


@app.get("/api/demo", tags=["Demo"])
def list_demos():
    """Lists all available demo scenario names and their product."""
    return {
        name: {"product": data.product_name, "event": data.local_event}
        for name, data in DEMO_SCENARIOS.items()
    }