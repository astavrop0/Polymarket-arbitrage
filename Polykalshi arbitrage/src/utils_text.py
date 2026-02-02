import json
import re

def normalize_title(s: str) -> str:
    """Normalize text for comparison"""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_number_from_text(text: str) -> float:
    """Extract a decimal number from text (e.g., '1.5', '3.5', '2', etc.)"""
    match = re.search(r'\b(\d+\.?\d*)\b', text)
    if match:
        return float(match.group(1))
    return None

def parse_outcome_prices(raw):
    """Parse Polymarket outcome prices"""
    try:
        if isinstance(raw, list):
            return [float(raw[0]), float(raw[1])]
        elif isinstance(raw, str):
            parsed = json.loads(raw)
            return [float(parsed[0]), float(parsed[1])]
        return None
    except (ValueError, IndexError, TypeError, json.JSONDecodeError):
        return None

def parse_token_ids(raw):
    """Parse Polymarket token IDs"""
    try:
        if isinstance(raw, list):
            return raw
        elif isinstance(raw, str):
            return json.loads(raw)
        return None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None

def parse_outcomes(raw):
    """Parse Polymarket outcomes array"""
    try:
        if isinstance(raw, list):
            return raw
        elif isinstance(raw, str):
            return json.loads(raw)
        return None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None