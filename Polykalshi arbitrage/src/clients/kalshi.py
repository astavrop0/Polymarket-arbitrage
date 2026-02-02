from collections import defaultdict
import requests

from src.config import KALSHI_API
from src.matching.rules import infer_kalshi_type


def fetch_kalshi_events_with_markets():
    """Fetch all Kalshi events with their markets, grouped by sport."""
    response = requests.get(f"{KALSHI_API}/search/filters_by_sport")
    filters_data = response.json()
    all_sports = [s for s in filters_data.get("sport_ordering", []) if s != "All sports"]

    events_by_sport = defaultdict(list)

    for sport in all_sports:
        response = requests.get(
            f"{KALSHI_API}/series", params={"category": "Sports", "tags": sport}
        )
        series_data = response.json().get("series", [])
        sport_tickers = [s.get("ticker") for s in series_data if s.get("ticker")]

        all_events = []
        for ticker in sport_tickers:
            cursor = None
            limit = 200
            while True:
                params = {
                    "status": "open",
                    "series_ticker": ticker,
                    "with_nested_markets": True,
                    "limit": limit,
                }
                if cursor:
                    params["cursor"] = cursor

                response = requests.get(f"{KALSHI_API}/events", params=params)
                data_response = response.json()
                events = data_response.get("events", [])

                if not events:
                    break

                all_events.extend(events)
                cursor = data_response.get("cursor")
                if not cursor:
                    break

        # EXCLUDE SPREAD EVENTS entirely
        for event in all_events:
            event_id = event.get("event_ticker", "")
            event_title = event.get("title", "")
            event_type = infer_kalshi_type(event_title)

            if event_type == "spreads":
                continue

            markets = []
            for market in event.get("markets", []):
                market_id = market.get("ticker", "")
                market_title = market.get("yes_sub_title", "")

                markets.append(
                    {
                        "market_id": market_id,
                        "title": market_title,
                        "yes_ask": float(market.get("yes_ask_dollars")),
                        "yes_bid": float(market.get("yes_bid_dollars")),
                        "no_ask": float(market.get("no_ask_dollars")),
                        "no_bid": float(market.get("no_bid_dollars")),
                        "volume": market.get("volume_24h", 0),
                    }
                )

            if markets:
                events_by_sport[sport].append(
                    {"event_id": event_id, "title": event_title, "markets": markets}
                )

    return events_by_sport