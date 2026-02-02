from fuzzywuzzy import fuzz

from src.utils_text import normalize_title
from src.matching.rules import extract_game_name, infer_kalshi_type, infer_poly_type


def match_events(poly_events, kalshi_events, threshold=70):
    """
    Match events between Polymarket and Kalshi.
    One Poly "More Markets" can match MULTIPLE Kalshi events (Totals, BTTS).

    Notes:
    - Uses fuzzy token_set_ratio on normalized game names.
    - Applies type compatibility (moneyline vs more_markets).
    - Enforces: each Kalshi event matched at most once;
      Poly moneyline events matched at most once.
    """
    matches = []

    for p in poly_events:
        poly_game = normalize_title(extract_game_name(p["title"], "polymarket"))
        poly_type = infer_poly_type(p["title"])

        for k in kalshi_events:
            kal_game = normalize_title(extract_game_name(k["title"], "kalshi"))
            kal_type = infer_kalshi_type(k["title"])

            # TYPE COMPATIBILITY
            if poly_type == "moneyline" and kal_type != "moneyline":
                continue
            if poly_type == "more_markets" and kal_type not in ["totals", "btts"]:
                continue

            score = fuzz.token_set_ratio(poly_game, kal_game)
            if score >= threshold:
                matches.append(
                    {
                        "poly": p,
                        "kalshi": k,
                        "score": score,
                        "poly_type": poly_type,
                        "kalshi_type": kal_type,
                    }
                )

    matches.sort(key=lambda x: x["score"], reverse=True)

    used_kalshi = set()
    used_poly_moneyline = set()
    final_matches = []

    for match in matches:
        poly_id = id(match["poly"])
        kalshi_id = id(match["kalshi"])
        poly_type = match["poly_type"]

        # Kalshi events can only be matched once
        if kalshi_id in used_kalshi:
            continue

        # Moneyline poly events can only match once
        if poly_type == "moneyline":
            if poly_id in used_poly_moneyline:
                continue
            used_poly_moneyline.add(poly_id)

        final_matches.append(match)
        used_kalshi.add(kalshi_id)

    return final_matches