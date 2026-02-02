from collections import defaultdict
import requests

from src.config import GAMMA_API, POLY_LEAGUE_TO_KALSHI_SPORT
from src.utils_text import parse_outcome_prices, parse_token_ids, parse_outcomes


def fetch_polymarket_events_with_markets():
    """Fetch all Polymarket events with their markets, grouped by sport."""
    sports = requests.get(f"{GAMMA_API}/sports").json()
    events_by_sport = defaultdict(list)

    max_limit = 200
    limit = 50

    for item in sports:
        series = item.get("series")
        league_code = item.get("sport")

        if not series or not league_code:
            continue

        try:
            series = int(series)
        except (TypeError, ValueError):
            continue

        league_code = league_code.lower()
        kalshi_sport = POLY_LEAGUE_TO_KALSHI_SPORT.get(league_code)

        if not kalshi_sport:
            continue

        page_id = 0
        while page_id < max_limit:
            resp = requests.get(
                f"{GAMMA_API}/events",
                params={
                    "series_id": series,
                    "active": True,
                    "closed": False,
                    "limit": limit,
                    "offset": page_id * limit,
                },
            )
            events = resp.json()
            if not events:
                break

            for event in events:
                event_title = event.get("title", "")
                event_slug = event.get("slug", "")

                markets = []
                for market in event.get("markets", []):
                    question = market.get("question")
                    raw_prices = market.get("outcomePrices")
                    parsed_prices = parse_outcome_prices(raw_prices)

                    raw_tokenIDs = market.get("clobTokenIds")
                    parsed_tokenIDs = parse_token_ids(raw_tokenIDs)

                    raw_outcomes = market.get("outcomes", [])
                    parsed_outcomes = parse_outcomes(raw_outcomes)

                    volume = market.get("volumeNum", 0)

                    if not question or not parsed_prices:
                        continue

                    # EXCLUDE SPREADS from Polymarket
                    if "spread" in question.lower() and "price spread" not in question.lower():
                        continue

                    markets.append(
                        {
                            "question": question,
                            "market_id": market.get("id"),
                            "market_slug": market.get("slug", ""),
                            "condition_id": market.get("conditionId"),
                            "outcome_prices": parsed_prices,
                            "token_ids": parsed_tokenIDs,
                            "outcomes": parsed_outcomes,
                            "volume_p": volume,
                        }
                    )

                if markets:
                    events_by_sport[kalshi_sport].append(
                        {"title": event_title, "slug": event_slug, "markets": markets}
                    )

            page_id += 1

    return events_by_sport