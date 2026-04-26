from models import ProductInput


def build_system_prompt() -> str:
    return """You are WarungAI, an expert business advisor for small Malaysian warung \
and retail shop owners. You specialise in pricing strategy, inventory management, \
and demand forecasting for the local Malaysian F&B and retail market.

You deeply understand Malaysian consumer behaviour, festive seasons (Hari Raya, \
Chinese New Year, Deepavali, school holidays), and local pricing dynamics.

Your role is to analyse product data and return ONLY a valid JSON object — \
no extra text, no markdown, no explanation outside the JSON.

Always give practical, actionable advice in simple English that a warung owner \
can immediately act on. Be specific with numbers."""


def build_user_prompt(data: ProductInput) -> str:
    margin = ((data.selling_price - data.cost_price) / data.selling_price) * 100
    vs_competitor = data.selling_price - data.competitor_price
    competitor_note = (
        f"RM{abs(vs_competitor):.2f} {'above' if vs_competitor > 0 else 'below'} competitor"
    )

    return f"""Analyze this product. Reply ONLY with a short JSON. No explanation outside JSON.

Product: {data.product_name}
Sold (7d): {data.units_sold_last_7_days} units
Stock: {data.current_stock} units
Cost: RM{data.cost_price:.2f} | Price: RM{data.selling_price:.2f} | Competitor: RM{data.competitor_price:.2f} ({competitor_note})
Margin: {margin:.1f}%
Event: {data.local_event or "None"} | Day: {data.day_type.value}
Note: {data.owner_note or "None"}

Return ONLY this JSON, keep each value under 15 words:
{{
  "demand_forecast": "high or medium or low",
  "price_recommendation": "one short action",
  "stock_recommendation": "one short action",
  "bundle_suggestion": "one idea or null",
  "reasoning": "one sentence only",
  "impact_estimate": "one number estimate"
}}"""

