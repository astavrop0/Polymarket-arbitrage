# src/matching/market_matching.py

from fuzzywuzzy import fuzz

from src.utils_text import normalize_title
from src.matching.rules import (
    is_soccer_sport,
    extract_outcome_from_poly_question,
    normalize_kalshi_subtitle,
)
from src.matching.name_mapping import NBA_POLY_TO_KALSHI_TEAM


def match_markets_within_event_soccer(poly_markets, kalshi_markets, threshold=60):
    """
    Match markets for Soccer.
    Totals are matched by EXACT number; non-totals use fuzzy matching.
    Each Kalshi market is matched to at most one Poly market (best score wins).
    """
    matched = []

    for poly_market in poly_markets:
        poly_question = poly_market["question"]
        poly_outcome_info = extract_outcome_from_poly_question(poly_question)

        best_match = None
        best_score = 0

        for kalshi_market in kalshi_markets:
            kalshi_subtitle = kalshi_market["title"]
            kalshi_info = normalize_kalshi_subtitle(kalshi_subtitle)

            # Totals: require exact number match
            if poly_outcome_info.get("type") == "totals" and kalshi_info.get("type") == "totals":
                if poly_outcome_info.get("number") == kalshi_info.get("number"):
                    score = 100
                else:
                    continue
            else:
                score = fuzz.token_set_ratio(
                    poly_outcome_info.get("normalized", ""),
                    kalshi_info.get("normalized", ""),
                )

            if score > best_score:
                best_score = score
                best_match = kalshi_market

        if best_match and best_score >= threshold:
            matched.append(
                {
                    "poly_market": poly_market,
                    "kalshi_market": best_match,
                    "score": best_score,
                }
            )

    # Deduplicate: each Kalshi market matches at most one Poly market (keep best)
    kalshi_to_best = {}
    for m in matched:
        kalshi_id = m["kalshi_market"]["market_id"]
        if kalshi_id not in kalshi_to_best or m["score"] > kalshi_to_best[kalshi_id]["score"]:
            kalshi_to_best[kalshi_id] = m

    return list(kalshi_to_best.values())


def match_markets_within_event_outcomes(
    poly_markets,
    kalshi_markets,
    threshold=70,
    apply_nba_mapping=False,
):
    """
    Match markets for non-soccer sports using outcome-based matching.

    Minimal NBA fix:
    - ONLY changes the Poly outcome string right before fuzzy matching
    - ONLY when apply_nba_mapping=True
    """
    matched = []

    for poly_market in poly_markets:
        outcomes = poly_market.get("outcomes", [])
        outcome_prices = poly_market.get("outcome_prices", [])

        if not outcomes:
            continue

        for i, outcome in enumerate(outcomes):
            # --- minimal change: only mutate string used for matching ---
            poly_outcome_for_match = (
                NBA_POLY_TO_KALSHI_TEAM.get(outcome.strip().lower(), outcome)
                if apply_nba_mapping
                else outcome
            )

            outcome_normalized = normalize_title(poly_outcome_for_match)
            outcome_price = outcome_prices[i] if i < len(outcome_prices) else None

            best_match = None
            best_score = 0

            for kalshi_market in kalshi_markets:
                kalshi_subtitle = normalize_title(kalshi_market["title"])
                score = fuzz.token_set_ratio(outcome_normalized, kalshi_subtitle)

                if score > best_score:
                    best_score = score
                    best_match = kalshi_market

            if best_match and best_score >= threshold:
                matched.append(
                    {
                        "poly_market": poly_market,
                        "kalshi_market": best_match,
                        "score": best_score,
                        "poly_outcome": outcome,
                        "poly_outcome_price": outcome_price,
                        "poly_outcome_index": i,
                    }
                )

    return matched


def match_markets_within_event(poly_markets, kalshi_markets, sport, poly_event_slug=None):
    """Route to appropriate market matching based on sport."""
    if is_soccer_sport(sport):
        return match_markets_within_event_soccer(poly_markets, kalshi_markets, threshold=60)

    apply_nba = bool(
        sport and sport.lower() == "basketball"
        and poly_event_slug
        and poly_event_slug.startswith("nba-")
    )

    return match_markets_within_event_outcomes(
        poly_markets,
        kalshi_markets,
        threshold=70,
        apply_nba_mapping=apply_nba,
    )