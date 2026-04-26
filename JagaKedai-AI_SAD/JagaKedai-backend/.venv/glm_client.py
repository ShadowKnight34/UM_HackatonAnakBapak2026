import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv
from models import ProductInput, AdvisorOutput, DemandLevel
from prompt_builder import build_system_prompt, build_user_prompt

# ─── CONFIG ───────────────────────────────────────────────────────────────────

load_dotenv()
ILMU_API_KEY  = os.getenv("ILMU_API_KEY", "")
ILMU_BASE_URL = os.getenv("ILMU_BASE_URL", "https://api.ilmu.ai/v1")
GLM_MODEL     = os.getenv("GLM_MODEL", "ilmu-glm-5.1")
USE_MOCK_GLM  = os.getenv("USE_MOCK_GLM", "false").lower() == "true"

TIMEOUT_SECONDS = 60


# ─── MOCK RESPONSE ────────────────────────────────────────────────────────────

def _mock_analyze(product: ProductInput) -> AdvisorOutput:
    """
    Generates a realistic mock response derived from the actual product data.
    Used when USE_MOCK_GLM=true in .env (e.g., while the hackathon API is down).
    """
    daily_avg   = product.units_sold_last_7_days / 7
    days_left   = product.current_stock / max(daily_avg, 0.1)
    margin_pct  = ((product.selling_price - product.cost_price) / product.selling_price) * 100
    comp_diff   = product.selling_price - product.competitor_price
    is_festive  = any(kw in (product.local_event or "").lower()
                      for kw in ["raya", "cny", "deepavali", "holiday", "christmas", "merdeka"])
    is_weekend  = product.day_type.value == "weekend"

    # Derive demand level from sales velocity and context
    if daily_avg >= 15 or is_festive or is_weekend:
        demand = DemandLevel.high
    elif daily_avg >= 7:
        demand = DemandLevel.medium
    else:
        demand = DemandLevel.low

    # Price recommendation
    if comp_diff > 0.50:
        price_rec = f"Lower price by RM{comp_diff:.2f} to match competitor and recover volume"
    elif comp_diff < -0.50 and (is_festive or demand == DemandLevel.high):
        price_rec = f"Increase price by RM{abs(comp_diff):.2f} — demand supports a premium"
    else:
        price_rec = "Maintain current price — you're competitively positioned"

    # Stock recommendation
    restock_qty = max(0, round((daily_avg * 7) - product.current_stock))
    if is_festive:
        restock_qty = round(restock_qty * 1.4)
    if days_left <= 2:
        stock_rec = f"Restock urgently — only {days_left:.1f} days of stock left. Order {restock_qty} units now"
    elif days_left <= 5:
        stock_rec = f"Restock soon — {days_left:.1f} days remaining. Order {restock_qty} units this week"
    else:
        stock_rec = f"Stock is adequate ({days_left:.1f} days). Reorder {restock_qty} units as routine"

    # Bundle suggestion
    bundles = {
        "Teh Ais": "Bundle Teh Ais + Nasi Lemak for RM4.50 — popular pairing",
        "Nasi Lemak": "Bundle Nasi Lemak + Teh Tarik for RM4.00 — great breakfast set",
        "Fries": "Bundle Fries + Burger for RM6.50 to move slow stock faster",
    }
    bundle = bundles.get(product.product_name,
                         f"Bundle {product.product_name} with a popular drink for a set deal")

    # Reasoning
    event_note = f" during {product.local_event}" if is_festive else ""
    reasoning  = (
        f"{product.product_name} shows {demand.value} demand{event_note} "
        f"with a {margin_pct:.0f}% margin and {days_left:.1f} days of stock remaining."
    )

    # Impact estimate
    weekly_profit = product.units_sold_last_7_days * (product.selling_price - product.cost_price)
    if demand == DemandLevel.high:
        impact = f"Estimated +RM{weekly_profit * 0.15:.0f} additional weekly profit with optimised pricing"
    else:
        impact = f"Stable weekly profit of approximately RM{weekly_profit:.0f} at current pace"

    return AdvisorOutput(
        demand_forecast=demand,
        price_recommendation=price_rec,
        stock_recommendation=stock_rec,
        bundle_suggestion=bundle,
        reasoning=reasoning,
        impact_estimate=impact,
    )


# ─── HEADERS ──────────────────────────────────────────────────────────────────

def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {ILMU_API_KEY}",
        "Content-Type": "application/json",
    }


# ─── HEALTH CHECK ─────────────────────────────────────────────────────────────

def check_glm_health() -> tuple[bool, str]:
    """
    Ping the GLM with a minimal message to confirm it's reachable.
    Returns (is_reachable: bool, message: str)
    """
    if USE_MOCK_GLM:
        return True, "Mock mode active — GLM calls are simulated (USE_MOCK_GLM=true)"

    try:
        response = requests.post(
            f"{ILMU_BASE_URL}/chat/completions",
            headers=_get_headers(),
            json={
                "model": GLM_MODEL,
                "messages": [{"role": "user", "content": "Reply with OK"}],
                "max_tokens": 10,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return True, f"GLM is reachable (model: {GLM_MODEL})"
        else:
            return False, f"GLM returned status {response.status_code}: {response.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to GLM API — check ILMU_BASE_URL"
    except requests.exceptions.Timeout:
        return False, "GLM API timed out on health check"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


# ─── CORE GLM CALL ────────────────────────────────────────────────────────────

def _call_glm(messages: list[dict], max_tokens: int = 1500) -> Optional[str]:
    """
    Raw call to the GLM. Returns the response text or raises an exception.
    """
    payload = {
        "model": GLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,  # low temp = more consistent, structured outputs
    }

    response = requests.post(
        f"{ILMU_BASE_URL}/chat/completions",
        headers=_get_headers(),
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    data = response.json()

    # Standard OpenAI-compatible response format
    if "choices" in data and len(data["choices"]) > 0:
        content = data["choices"][0].get("message", {}).get("content")
        if content is None:
            raise ValueError(f"No content in GLM response: {data}")
        return content
    else:
        raise ValueError(f"Unexpected GLM response structure: {data}")


# ─── PARSE GLM RESPONSE ───────────────────────────────────────────────────────

def _parse_glm_response(raw_text: str) -> AdvisorOutput:
    """
    Safely parse the GLM JSON response into AdvisorOutput.
    Strips markdown fences if the model wraps output in ```json ... ```
    """
    if raw_text is None:
        raise ValueError("GLM returned None — response is empty")

    # Strip markdown fences if present
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1])

    parsed = json.loads(cleaned)

    return AdvisorOutput(
        demand_forecast=parsed["demand_forecast"],
        price_recommendation=parsed["price_recommendation"],
        stock_recommendation=parsed["stock_recommendation"],
        bundle_suggestion=parsed.get("bundle_suggestion"),
        reasoning=parsed["reasoning"],
        impact_estimate=parsed["impact_estimate"],
    )


# ─── MAIN FUNCTION: ANALYZE PRODUCT ──────────────────────────────────────────

def analyze_product(product: ProductInput) -> AdvisorOutput:
    """
    Full pipeline: build prompt → call GLM → parse response → return AdvisorOutput.
    If USE_MOCK_GLM=true in .env, returns a context-aware mock response instead.
    Raises an exception if anything fails (caught in main.py).
    """
    if USE_MOCK_GLM:
        return _mock_analyze(product)

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user",   "content": build_user_prompt(product)},
    ]

    raw_response = _call_glm(messages)
    return _parse_glm_response(raw_response)

