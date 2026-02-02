Polykalshi arbitrage/
│
└── src/
    │
    ├── __init__.py
    │
    ├── run_pipeline.py
    │   • Main runner / orchestration  
    │   • Fetches data, matches events and markets  
    │   • Builds DataFrames and prints summaries  
    │
    ├── config.py
    │   • Configuration constants  
    │   • API endpoints (Kalshi, Polymarket)  
    │   • League → sport mapping  
    │
    ├── utils_text.py
    │   • Pure text utilities  
    │   • Normalization and small parsers used across the project  
    │
    ├── clients/
    │   ├── __init__.py
    │   ├── polymarket.py
    │   │   • fetch_polymarket_events_with_markets()
    │   │   • All Polymarket API interaction and parsing  
    │   │
    │   └── kalshi.py
    │       • fetch_kalshi_events_with_markets()
    │       • All Kalshi API interaction and parsing  
    │
    ├── matching/
    │   ├── __init__.py
    │   ├── rules.py
    │   │   • Title/question interpretation rules  
    │   │   • Sport-specific parsing logic  
    │   │
    │   ├── event_matching.py
    │   │   • match_events()
    │   │   • Fuzzy matching between Polymarket and Kalshi events  
    │   │
    │   └── market_matching.py
    │       • match_markets_within_event_soccer()
    │       • match_markets_within_event_outcomes()
    │       • match_markets_within_event() (router)  
    │
    └── notebooks/
        └── testing.ipynb
            • Interactive notebook for exploration and debugging