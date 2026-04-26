import numpy as np
from models import ProductInput


# ─── CORE METRICS ─────────────────────────────────────────────────────────────

def calculate_metrics(product: ProductInput) -> dict:
    """
    Pre-calculates business metrics from raw product input.
    Returns a dict of numbers ready for the frontend to display as cards/charts.
    """
    daily_avg = product.units_sold_last_7_days / 7
    days_of_stock = product.current_stock / max(daily_avg, 0.1)
    margin_pct = ((product.selling_price - product.cost_price) / product.selling_price) * 100
    weekly_revenue = product.units_sold_last_7_days * product.selling_price
    weekly_profit = product.units_sold_last_7_days * (product.selling_price - product.cost_price)
    competitor_diff = product.selling_price - product.competitor_price
    competitor_diff_pct = (competitor_diff / product.competitor_price) * 100

    # Stock urgency level
    if days_of_stock <= 2:
        stock_urgency = "critical"
    elif days_of_stock <= 5:
        stock_urgency = "low"
    elif days_of_stock <= 10:
        stock_urgency = "moderate"
    else:
        stock_urgency = "sufficient"

    # Pricing position vs competitor
    if competitor_diff > 0.5:
        pricing_position = "overpriced"
    elif competitor_diff < -0.5:
        pricing_position = "underpriced"
    else:
        pricing_position = "competitive"

    return {
        # Sales metrics
        "daily_avg_sales": round(daily_avg, 1),
        "weekly_units_sold": product.units_sold_last_7_days,

        # Stock metrics
        "days_of_stock_left": round(days_of_stock, 1),
        "current_stock": product.current_stock,
        "stock_urgency": stock_urgency,               # critical / low / moderate / sufficient

        # Financial metrics
        "margin_percent": round(margin_pct, 1),
        "weekly_revenue": round(weekly_revenue, 2),
        "weekly_profit": round(weekly_profit, 2),
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,

        # Competitor metrics
        "competitor_price": product.competitor_price,
        "competitor_diff": round(competitor_diff, 2),       # positive = you're more expensive
        "competitor_diff_pct": round(competitor_diff_pct, 1),
        "pricing_position": pricing_position,               # overpriced / underpriced / competitive
    }


# ─── SIMULATED WEEKLY TREND ───────────────────────────────────────────────────

def generate_weekly_trend(product: ProductInput) -> list[dict]:
    """
    Simulates a 7-day sales trend for chart display.
    Uses the 7-day total and adds realistic daily variation using numpy.
    Returns a list of 7 dicts with 'day' and 'units_sold'.
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Realistic weights — weekends sell more
    weights = np.array([0.85, 0.80, 0.90, 0.95, 1.10, 1.30, 1.10])
    weights = weights / weights.sum()  # normalize to sum to 1

    # Scale to match actual weekly total
    daily_units = np.round(weights * product.units_sold_last_7_days).astype(int)

    # Fix rounding drift so total matches exactly
    diff = product.units_sold_last_7_days - daily_units.sum()
    daily_units[-1] += diff

    return [
        {"day": days[i], "units_sold": int(daily_units[i])}
        for i in range(7)
    ]


# ─── RESTOCK RECOMMENDATION ───────────────────────────────────────────────────

def calculate_restock_quantity(product: ProductInput, buffer_days: int = 7) -> dict:
    """
    Calculates how many units to restock based on daily average + buffer.
    buffer_days: how many days of stock to maintain (default 7)
    """
    daily_avg = product.units_sold_last_7_days / 7

    # Boost daily avg if festive event
    event = (product.local_event or "").lower()
    festive_keywords = ["raya", "cny", "deepavali", "holiday", "christmas", "merdeka"]
    is_festive = any(kw in event for kw in festive_keywords)
    if is_festive:
        daily_avg *= 1.4  # 40% boost during festive seasons

    target_stock = daily_avg * buffer_days
    restock_needed = max(0, target_stock - product.current_stock)
    restock_cost = restock_needed * product.cost_price

    return {
        "restock_quantity": round(restock_needed),
        "target_stock_level": round(target_stock),
        "restock_cost_estimate": round(restock_cost, 2),
        "is_festive_adjusted": is_festive,
        "buffer_days": buffer_days,
    }

