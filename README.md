# Polykalshi Arbitrage

A Python project to fetch sports prediction markets from **Polymarket** and **Kalshi**, match corresponding events and markets across platforms using fuzzy and rule-based logic, and analyze price differences.

---

## 🚀 What this project does

The pipeline:

1. **Fetches** active sports markets from Polymarket and Kalshi  
2. **Matches** corresponding events across platforms  
3. **Matches markets within events** (soccer handled differently from other sports)  
4. **Aggregates results into DataFrames** for analysis  
5. **Prints summaries** and keeps track of problematic cases  

---

## 📁 Project Structure (current state)

```text
Polykalshi arbitrage/
└── src/
    ├── __init__.py
    ├── run_pipeline.py
    ├── config.py
    ├── utils_text.py
    ├── clients/
    │   ├── __init__.py
    │   ├── polymarket.py
    │   └── kalshi.py
    ├── matching/
    │   ├── __init__.py
    │   ├── rules.py
    │   ├── event_matching.py
    │   └── market_matching.py
    └── notebooks/
        └── testing.ipynb
```

---

## 🧩 What each part does

### **Runner (orchestration)**
**`src/run_pipeline.py`**
- Coordinates the full workflow: fetch → match → aggregate → report  
- Builds three key DataFrames:
  - `df_matched_markets`
  - `df_event_summary`
  - `df_debug_no_markets`  
- Contains only high-level logic (no API calls or matching internals).

---

### **Configuration**
**`src/config.py`**
- API endpoints for:
  - Kalshi  
  - Polymarket  
- League → sport mapping (`POLY_LEAGUE_TO_KALSHI_SPORT`).

---

### **Utilities**
**`src/utils_text.py`**
Reusable text helpers used across the project:
- Normalization
- Extracting numbers from text
- Parsing Polymarket JSON fields

---

### **Clients (data ingestion)**

**`src/clients/polymarket.py`**
- `fetch_polymarket_events_with_markets()`
- Handles Polymarket API calls, pagination, and parsing.

**`src/clients/kalshi.py`**
- `fetch_kalshi_events_with_markets()`
- Handles Kalshi API calls, pagination, and parsing.
- Excludes spread markets at source.

---

### **Matching logic**

**`src/matching/rules.py`**
- Interprets titles and questions:
  - Event type detection  
  - Soccer-specific parsing (totals, BTTS, etc.)

**`src/matching/event_matching.py`**
- `match_events()`
- Fuzzy matching of Polymarket vs Kalshi events using normalized titles and compatibility rules.

**`src/matching/market_matching.py`**
- Soccer matching:
  - Exact matching for totals (e.g., 2.5 vs 2.5)
  - Fuzzy matching for other outcomes  
- Other sports:
  - Outcome-based fuzzy matching  
- Router to choose the correct method per sport.

---

### **Notebook**
**`notebooks/testing.ipynb`**
- Interactive workspace to:
  - Inspect raw API data
  - Debug mismatches
  - Test matching logic step by step
  - Analyze results without rerunning the whole pipeline every time.

---

## ▶️ How to run the pipeline

From the project root:

```bash
python -m src.run_pipeline
```

This will:
- Fetch data from both platforms,
- Perform event and market matching,
- Print summaries to the terminal.

---

## 🧪 How to use the notebook

Open in Jupyter / VS Code / JupyterLab:

```
notebooks/testing.ipynb
```

A typical starting point inside the notebook:

```python
from src.clients.polymarket import fetch_polymarket_events_with_markets
from src.clients.kalshi import fetch_kalshi_events_with_markets
from src.matching.event_matching import match_events
from src.matching.market_matching import match_markets_within_event
```

---

## 📦 Dependencies

You need at least:

```
pandas
requests
fuzzywuzzy
python-Levenshtein   # optional but recommended (faster matching)
```

Install with:

```bash
pip install pandas requests fuzzywuzzy python-Levenshtein
```
