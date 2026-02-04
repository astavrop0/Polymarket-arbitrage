import re
from src.utils_text import normalize_title, extract_number_from_text
from src.matching.name_mapping import map_polymarket_nba_title

def extract_game_name(title: str, platform: str, poly_slug: str | None = None) -> str:
    """Extract canonical game name from event title (optionally using poly_slug for NBA mapping)."""
    if platform == "polymarket":
        # apply NBA nickname->city mapping ONLY for nba-* slugs
        title = map_polymarket_nba_title(title, poly_slug=poly_slug)

        if " - More Markets" in title:
            return title.replace(" - More Markets", "").strip()
        return title

    elif platform == "kalshi":
        if ":" in title:
            return title.split(":")[0].strip()
        return title

    return title

def infer_kalshi_type(title: str) -> str:
    """Infer Kalshi event type from title"""
    t = title.lower()
    if "both teams to score" in t or "btts" in t:
        return "btts"
    if "total" in t or ("over" in t and "goal" in t):
        return "totals"
    if "spread" in t or "cover" in t or "wins by" in t:
        return "spreads"
    return "moneyline"

def infer_poly_type(title: str) -> str:
    """Infer Polymarket event type from title"""
    return "more_markets" if "More Markets" in title else "moneyline"

def is_soccer_sport(sport: str) -> bool:
    """Check if sport uses soccer-style matching"""
    return sport.lower() == "soccer"

def extract_outcome_from_poly_question(question: str) -> dict:
    """
    Extract outcome from Polymarket question with NUMBER for totals.
    """
    question_lower = question.lower()

    # Check for draw/tie
    if "draw" in question_lower or "tie" in question_lower:
        return {"type": "draw", "normalized": "draw tie"}

    # Check for O/U with NUMBER
    if "o/u" in question_lower or ("over" in question_lower or "under" in question_lower):
        number = extract_number_from_text(question)
        if number is not None:
            return {"type": "totals", "number": number, "normalized": f"total {number}"}

    # Check for BTTS
    if "both teams" in question_lower and "score" in question_lower:
        return {"type": "btts", "normalized": "both teams to score"}

    # Extract team name from "Will [TEAM] win" pattern
    win_pattern = r"will\s+([\w\s]+?)\s+(?:win|fc win|united win)"
    match = re.search(win_pattern, question_lower)
    if match:
        team = match.group(1).strip()
        team = re.sub(r"\s+(fc|united|city|afc|cf)$", "", team).strip()
        return {"type": "team", "team": team, "normalized": normalize_title(team)}

    return {"type": "other", "normalized": normalize_title(question)}

def normalize_kalshi_subtitle(subtitle: str) -> dict:
    """
    Normalize Kalshi subtitle with NUMBER for totals.
    """
    normalized = normalize_title(subtitle)

    if normalized == "tie":
        return {"type": "tie", "normalized": "draw tie"}

    # Extract number for totals
    if "over" in normalized or "under" in normalized or "goals" in normalized or "total" in normalized:
        number = extract_number_from_text(subtitle)
        if number is not None:
            return {"type": "totals", "number": number, "normalized": f"total {number}"}

    # BTTS
    if "both teams" in normalized and "score" in normalized:
        return {"type": "btts", "normalized": "both teams to score"}

    return {"type": "other", "normalized": normalized}