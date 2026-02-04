# src/matching/name_mapping.py
import re
from typing import Optional

# Map Polymarket NBA nicknames -> Kalshi city-style tokens
# (Kalshi uses city tokens, including "Los Angeles L" and "Los Angeles C".)
NBA_POLY_TO_KALSHI_TEAM = {
    "hawks": "Atlanta",
    "celtics": "Boston",
    "nets": "Brooklyn",
    "hornets": "Charlotte",
    "bulls": "Chicago",
    "cavaliers": "Cleveland",
    "mavericks": "Dallas",
    "nuggets": "Denver",
    "pistons": "Detroit",
    "warriors": "Golden State",
    "rockets": "Houston",
    "pacers": "Indiana",
    "clippers": "Los Angeles C",
    "lakers": "Los Angeles L",
    "grizzlies": "Memphis",
    "heat": "Miami",
    "bucks": "Milwaukee",
    "timberwolves": "Minnesota",
    "pelicans": "New Orleans",
    "knicks": "New York",
    "thunder": "Oklahoma City",
    "magic": "Orlando",
    "76ers": "Philadelphia",
    "sixers": "Philadelphia",
    "suns": "Phoenix",
    "trail blazers": "Portland",
    "blazers": "Portland",
    "kings": "Sacramento",
    "spurs": "San Antonio",
    "raptors": "Toronto",
    "jazz": "Utah",
    "wizards": "Washington",
}

_MORE_MARKETS_RE = re.compile(r"\s*-\s*more\s+markets\s*$", re.IGNORECASE)

def _is_poly_nba(poly_slug: Optional[str]) -> bool:
    return bool(poly_slug) and poly_slug.lower().startswith("nba-")

def map_polymarket_nba_title(title: str, poly_slug: Optional[str] = None) -> str:
    """
    If this is a Polymarket NBA event (slug starts with nba-), rewrite
    'Nuggets vs Pistons' -> 'Denver vs Detroit' (and preserve ' - More Markets').
    Otherwise return title unchanged.
    """
    if not _is_poly_nba(poly_slug):
        return title

    # preserve suffix
    had_more = bool(_MORE_MARKETS_RE.search(title))
    base = _MORE_MARKETS_RE.sub("", title).strip()

    # expected Poly NBA format: 'X vs. Y' (sometimes 'vs' without dot)
    # Keep it conservative: if we can't split cleanly, don't touch it.
    m = re.split(r"\s+vs\.?\s+", base, flags=re.IGNORECASE)
    if len(m) != 2:
        return title

    t1, t2 = m[0].strip(), m[1].strip()

    def to_kalshi_team(token: str) -> str:
        key = token.lower().strip()
        # allow multi-word nicknames like "Trail Blazers"
        if key in NBA_POLY_TO_KALSHI_TEAM:
            return NBA_POLY_TO_KALSHI_TEAM[key]
        # allow last-word nickname if user ever has "Denver Nuggets"
        last = key.split()[-1]
        return NBA_POLY_TO_KALSHI_TEAM.get(last, token)

    new_base = f"{to_kalshi_team(t1)} vs {to_kalshi_team(t2)}"
    if had_more:
        new_base += " - More Markets"
    return new_base