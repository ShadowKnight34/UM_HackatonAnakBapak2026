# 🍜 FnB AI Advisor — Backend

> AI-powered pricing and inventory decision system for Malaysian warung & retail owners.  
> Built for **UMHackathon 2026 — Domain 2: AI for Economic Empowerment & Decision Intelligence**  
> Powered by **Z.AI GLM** via the ILMU API.

---

## 📁 Project Structure

```
fnb-ai-advisor/
├── main.py              # FastAPI app — all API routes
├── glm_client.py        # Z.AI GLM integration + mock fallback
├── prompt_builder.py    # Prompt construction for the GLM
├── models.py            # Pydantic input/output schemas
├── data_processor.py    # Math-only metrics (no AI needed)
├── demo_data.py         # 3 pre-built demo scenarios
├── requirements.txt     # Python dependencies
├── .env                 # API keys — NEVER push to GitHub
└── .gitignore
```

---

## ⚙️ Backend Setup

### Requirements
- Python **3.10+** (tested on 3.14)
- `pydantic >= 2.0` — **do not pin to 1.x**, it will break on Python 3.12+

### 1. Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```
> ⚠️ Always create the venv with the final folder name. **Do not rename venv folders** — Windows embeds the Python path into the launcher scripts at creation time.

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Set up `.env`
```env
ILMU_API_KEY=your_api_key_here
ILMU_BASE_URL=https://api.ilmu.ai/v1
GLM_MODEL=ilmu-glm-5.1
USE_MOCK_GLM=false
```
> Set `USE_MOCK_GLM=true` while the API is unavailable — the system returns realistic context-aware responses derived from the actual input data. **Flip to `false` on demo day.**

### 4. Start the server
```powershell
uvicorn main:app --reload --port 8000
```

### 5. Verify it's running
```powershell
curl http://localhost:8000/api/health
```
Expected response:
```json
{
  "status": "ok",
  "glm_reachable": true,
  "message": "GLM is reachable (model: ilmu-glm-5.1)"
}
```

Interactive API docs available at: **http://localhost:8000/docs**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Check server + GLM connectivity |
| `POST` | `/api/analyze` | Send product data → get AI decisions |
| `POST` | `/api/metrics` | Send product data → get calculated metrics |
| `GET` | `/api/demo/{scenario}` | Run a pre-built demo scenario |
| `GET` | `/api/demo` | List all demo scenario names |

---

## 📤 POST `/api/analyze` — Main AI Endpoint

Send product data, receive AI-powered recommendations from Z.AI GLM.  
**Expect 5–15 seconds response time** — show a loading spinner on the frontend.

### Request Body
```json
{
  "product_name": "Teh Ais",
  "units_sold_last_7_days": 120,
  "current_stock": 40,
  "cost_price": 0.80,
  "selling_price": 2.50,
  "competitor_price": 2.40,
  "local_event": "Hari Raya",
  "day_type": "weekend",
  "owner_note": "Open extended hours during festive week"
}
```

### Request Field Reference
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_name` | string | ✅ | Name of the product |
| `units_sold_last_7_days` | int ≥ 0 | ✅ | Units sold in the last 7 days |
| `current_stock` | int ≥ 0 | ✅ | Units currently in stock |
| `cost_price` | float > 0 | ✅ | Cost price in RM |
| `selling_price` | float > 0 | ✅ | Selling price in RM |
| `competitor_price` | float > 0 | ✅ | Nearby competitor's price in RM |
| `local_event` | string | optional | e.g. `"Hari Raya"`, `"none"` |
| `day_type` | `"weekday"` \| `"weekend"` | optional | Defaults to `"weekday"` |
| `owner_note` | string | optional | Any extra context from the owner |

### Response
```json
{
  "success": true,
  "product": "Teh Ais",
  "result": {
    "demand_forecast": "high",
    "price_recommendation": "Maintain current price — you're competitively positioned",
    "stock_recommendation": "Restock soon — 2.3 days remaining. Order 112 units this week",
    "bundle_suggestion": "Bundle Teh Ais + Nasi Lemak for RM4.50 — popular pairing",
    "reasoning": "Teh Ais shows high demand during Hari Raya with a 68% margin and 2.3 days of stock remaining.",
    "impact_estimate": "Estimated +RM31 additional weekly profit with optimised pricing"
  }
}
```

---

## 📊 POST `/api/metrics` — Dashboard Metrics Endpoint

Returns **pre-calculated numbers** for displaying charts and stat cards.  
**No AI call — instant response.** Call this first before `/api/analyze`.

### Request Body
Same shape as `/api/analyze`.

### Response
```json
{
  "product": "Teh Ais",
  "metrics": {
    "daily_avg_sales": 17.1,
    "weekly_units_sold": 120,
    "days_of_stock_left": 2.3,
    "current_stock": 40,
    "stock_urgency": "critical",
    "margin_percent": 68.0,
    "weekly_revenue": 300.00,
    "weekly_profit": 204.00,
    "cost_price": 0.80,
    "selling_price": 2.50,
    "competitor_price": 2.40,
    "competitor_diff": 0.10,
    "competitor_diff_pct": 4.2,
    "pricing_position": "competitive"
  },
  "weekly_trend": [
    { "day": "Mon", "units_sold": 14 },
    { "day": "Tue", "units_sold": 13 },
    { "day": "Wed", "units_sold": 15 },
    { "day": "Thu", "units_sold": 16 },
    { "day": "Fri", "units_sold": 18 },
    { "day": "Sat", "units_sold": 22 },
    { "day": "Sun", "units_sold": 22 }
  ],
  "restock": {
    "restock_quantity": 112,
    "target_stock_level": 152,
    "restock_cost_estimate": 89.60,
    "is_festive_adjusted": true,
    "buffer_days": 7
  }
}
```

### Stock Urgency Values
| Value | Meaning |
|-------|---------|
| `critical` | ≤ 2 days of stock left — restock immediately |
| `low` | 2–5 days — restock this week |
| `moderate` | 5–10 days — plan a reorder |
| `sufficient` | > 10 days — no action needed |

### Pricing Position Values
| Value | Meaning |
|-------|---------|
| `overpriced` | Your price is RM0.50+ above competitor |
| `underpriced` | Your price is RM0.50+ below competitor |
| `competitive` | Within RM0.50 of competitor |

---

## 🎮 Demo Scenarios

Pre-built test cases — use these during the hackathon demo.

| Name | Product | Best For |
|------|---------|----------|
| `normal_day` | Nasi Lemak | Baseline / weekday demo |
| `festive_season` | Teh Ais (Hari Raya) | **⭐ Use this first for judges** |
| `slow_moving` | Fries (excess stock) | Waste detection demo |

```powershell
# Test all 3
curl http://localhost:8000/api/demo/festive_season
curl http://localhost:8000/api/demo/normal_day
curl http://localhost:8000/api/demo/slow_moving
```

---

## 🎨 Frontend Integration Guide

> **For the React guy** — everything you need to connect to this backend.

### Base URL
```
http://localhost:8000
```

### Recommended Call Flow
```
1. User fills the input form
2. POST /api/metrics  → render stat cards + bar chart INSTANTLY
3. POST /api/analyze  → render AI recommendations (show spinner, 5–15s)
4. Both results displayed together on the dashboard
```

### Suggested UI Components

**Stat Cards** (from `/api/metrics → metrics`):
| Card | Field | Color rule |
|------|-------|------------|
| Daily Avg Sales | `daily_avg_sales` | Neutral |
| Days of Stock Left | `days_of_stock_left` | 🔴 if `stock_urgency === "critical"`, 🟡 if `"low"` |
| Weekly Profit | `weekly_profit` | Green |
| Margin % | `margin_percent` | Green |

**Bar Chart** (from `/api/metrics → weekly_trend`):
- X-axis: `day` (Mon–Sun)
- Y-axis: `units_sold`
- Highlight Saturday/Sunday bars

**Competitor Badge** (from `/api/metrics → metrics`):
- Show `pricing_position` as a badge: `OVERPRICED` / `COMPETITIVE` / `UNDERPRICED`
- Show `competitor_diff`: e.g. `RM0.10 above competitor`

**Restock Alert** (from `/api/metrics → restock`):
- Show if `restock_quantity > 0`
- Display `restock_quantity` and `restock_cost_estimate`
- Add festive badge if `is_festive_adjusted === true`

**AI Recommendation Panel** (from `/api/analyze → result`):
| Component | Field | Notes |
|-----------|-------|-------|
| Demand badge | `demand_forecast` | `HIGH` = red, `MEDIUM` = yellow, `LOW` = grey |
| Price advice | `price_recommendation` | Action card |
| Stock advice | `stock_recommendation` | Action card |
| Bundle idea | `bundle_suggestion` | Optional — show if not null |
| Reasoning | `reasoning` | Explanatory text |
| Impact | `impact_estimate` | **Highlight this — judges love it** |

### Loading State
```jsx
// GLM can take 5–15 seconds
const [analyzing, setAnalyzing] = useState(false);

// Show spinner on Analyze button while waiting
{analyzing ? <Spinner /> : <Button>Analyze</Button>}
```

### Error Handling
```js
// /api/analyze can fail if GLM is down
if (!response.ok) {
  const err = await response.json();
  showError(err.detail); // e.g. "GLM call failed: ..."
}
```

### Example Fetch Calls
```js
// Step 1 — get metrics instantly
const metricsRes = await fetch('http://localhost:8000/api/metrics', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData),
});
const { metrics, weekly_trend, restock } = await metricsRes.json();

// Step 2 — get AI analysis (takes longer)
setAnalyzing(true);
const analyzeRes = await fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(formData),
});
const { result } = await analyzeRes.json();
setAnalyzing(false);
```

---

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ILMU_API_KEY` | API key from hackathon organiser | `sk-xxxxx` |
| `ILMU_BASE_URL` | Z.AI GLM base URL | `https://api.ilmu.ai/v1` |
| `GLM_MODEL` | Model name (confirm from Discord) | `ilmu-glm-5.1` |
| `USE_MOCK_GLM` | `true` = smart mock responses, `false` = real GLM | `false` |

---

## 👥 Team Roles

| Role | Responsibility |
|------|---------------|
| Backend / AI Engineer | ✅ Done — GLM integration, all API endpoints, data processing, mock mode |
| Frontend | React UI, input form, stat cards, bar chart, AI recommendation display |
| Team Leader | System design, documentation, presentation deck |

---

## ✅ Demo Day Checklist

- [ ] Set `USE_MOCK_GLM=false` in `.env`
- [ ] Run `curl http://localhost:8000/api/health` → confirm `"glm_reachable": true`
- [ ] Test all 3 demo scenarios end-to-end
- [ ] Confirm `.env` is NOT pushed to GitHub
- [ ] Have `festive_season` demo loaded and ready to go first

---

*Built with FastAPI + Pydantic v2 + Z.AI GLM for UMHackathon 2026*

