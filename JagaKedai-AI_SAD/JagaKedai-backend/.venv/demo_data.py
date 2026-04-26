from models import ProductInput, DayType

# ─────────────────────────────────────────────────────────────────────────────
# 3 Demo Scenarios for your hackathon demo video & testing
# Use these to fire reliable, impressive outputs during the presentation
# ─────────────────────────────────────────────────────────────────────────────

DEMO_SCENARIOS = {

    # ── Scenario 1: Normal Business Day ─────────────────────────────────────
    "normal_day": ProductInput(
        product_name="Nasi Lemak",
        units_sold_last_7_days=70,
        current_stock=50,
        cost_price=1.20,
        selling_price=3.00,
        competitor_price=3.00,
        local_event="none",
        day_type=DayType.weekday,
        owner_note="Sells well in the morning",
    ),

    # ── Scenario 2: Festive Season — BEST DEMO SCENARIO ─────────────────────
    "festive_season": ProductInput(
        product_name="Teh Ais",
        units_sold_last_7_days=120,
        current_stock=40,
        cost_price=0.80,
        selling_price=2.50,
        competitor_price=2.40,
        local_event="Hari Raya",
        day_type=DayType.weekend,
        owner_note="Open extended hours during festive week",
    ),

    # ── Scenario 3: Slow-Moving / Waste Detection ────────────────────────────
    "slow_moving": ProductInput(
        product_name="Fries",
        units_sold_last_7_days=10,
        current_stock=80,
        cost_price=1.50,
        selling_price=4.00,
        competitor_price=3.50,
        local_event="none",
        day_type=DayType.weekday,
        owner_note="Bought extra stock last week, not selling well",
    ),
}


def get_demo(scenario_name: str) -> ProductInput:
    """
    Retrieve a demo scenario by name.
    Valid names: 'normal_day', 'festive_season', 'slow_moving'
    """
    if scenario_name not in DEMO_SCENARIOS:
        raise ValueError(
            f"Unknown scenario '{scenario_name}'. "
            f"Valid options: {list(DEMO_SCENARIOS.keys())}"
        )
    return DEMO_SCENARIOS[scenario_name]
