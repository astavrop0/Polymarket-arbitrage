import pandas as pd

from src.clients.polymarket import fetch_polymarket_events_with_markets
from src.clients.kalshi import fetch_kalshi_events_with_markets
from src.matching.event_matching import match_events
from src.matching.market_matching import match_markets_within_event
from src.matching.rules import is_soccer_sport

# =========================
# MAIN EXECUTION
# =========================
def main():
    print("Fetching Polymarket events with markets...")
    poly_events_by_sport = fetch_polymarket_events_with_markets()

    print("Fetching Kalshi events with markets...")
    kalshi_events_by_sport = fetch_kalshi_events_with_markets()

    print("\nMatching events and markets...")

    all_matched_data = []
    event_match_summary = []
    debug_no_markets = []

    for sport in poly_events_by_sport.keys():
        if sport not in kalshi_events_by_sport:
            continue
        
        poly_events = poly_events_by_sport[sport]
        kalshi_events = kalshi_events_by_sport[sport]
        
        #event_matches = match_events(poly_events, kalshi_events, threshold=70)
        event_threshold = 90 if sport == "Soccer" else 70
        event_matches = match_events(poly_events, kalshi_events, threshold=event_threshold)

        for event_match in event_matches:
            poly_event = event_match["poly"]
            kalshi_event = event_match["kalshi"]
            
            event_match_summary.append({
                'sport': sport,
                'poly_event_title': poly_event["title"],
                'poly_event_slug': poly_event.get("slug", ""),
                'kalshi_event_title': kalshi_event["title"],
                'poly_markets_count': len(poly_event["markets"]),
                'kalshi_markets_count': len(kalshi_event["markets"]),
                'event_match_score': event_match["score"]
            })
            
            market_matches = match_markets_within_event(
                poly_event["markets"],
                kalshi_event["markets"],
                sport
            )
            
            if not market_matches:
                debug_no_markets.append({
                    'sport': sport,
                    'poly_event': poly_event["title"],
                    'poly_event_slug': poly_event.get("slug", ""),
                    'kalshi_event': kalshi_event["title"],
                    'poly_markets': len(poly_event["markets"]),
                    'kalshi_markets': len(kalshi_event["markets"]),
                    'sample_poly_question': poly_event["markets"][0]["question"] if poly_event["markets"] else "N/A",
                    'sample_poly_outcomes': str(poly_event["markets"][0].get("outcomes", [])) if poly_event["markets"] else "N/A",
                    'sample_kalshi_title': kalshi_event["markets"][0]["title"] if kalshi_event["markets"] else "N/A"
                })
            
            for market_match in market_matches:
                poly_market = market_match["poly_market"]
                kalshi_market = market_match["kalshi_market"]
                
                if not is_soccer_sport(sport) and "poly_outcome_price" in market_match:
                    poly_yes_price = market_match["poly_outcome_price"]
                    poly_no_price = 1 - poly_yes_price if poly_yes_price else None
                    poly_display_question = f"{poly_market['question']} - {market_match['poly_outcome']}"
                    poly_volume = poly_market.get("volume_p", 0)
                else:
                    poly_prices = poly_market.get("outcome_prices", [None, None])
                    poly_yes_price = poly_prices[0] if len(poly_prices) > 0 else None
                    poly_no_price = poly_prices[1] if len(poly_prices) > 1 else None
                    poly_display_question = poly_market["question"]
                    poly_volume = poly_market.get("volume_p", 0) 
                
                # UPDATED: Use direct Kalshi dollar prices (no calculation needed)
                kalshi_yes_ask = kalshi_market.get("yes_ask")
                kalshi_yes_bid = kalshi_market.get("yes_bid")
                kalshi_no_ask = kalshi_market.get("no_ask")
                kalshi_no_bid = kalshi_market.get("no_bid")
                kalshi_volume = kalshi_market.get("volume")
                
                # Calculate price spread using yes_ask prices
                price_spread = None
                if poly_yes_price is not None and kalshi_yes_bid is not None:
                    price_spread = abs(poly_yes_price - kalshi_yes_ask)
                
                all_matched_data.append({
                    "sport": sport,
                    "poly_event_title": poly_event["title"],
                    "kalshi_event_title": kalshi_event["title"],
                    "poly_market_slug": poly_market.get("market_slug", ""),
                    "poly_market_question": poly_display_question,
                    "kalshi_market_title": kalshi_market["title"],
                    "poly_yes_price": poly_yes_price,
                    "poly_no_price": poly_no_price,
                    "kalshi_yes_ask": kalshi_yes_ask,  # UPDATED
                    "kalshi_yes_bid": kalshi_yes_bid,  # UPDATED
                    "kalshi_no_ask": kalshi_no_ask,    # UPDATED
                    "kalshi_no_bid": kalshi_no_bid,    # UPDATED
                    "price_spread": price_spread,
                    "poly_volume24h": poly_volume,          
                    "kalshi_volume24h": kalshi_volume,
                    #"market_match_score": market_match["score"],
                    #"kalshi_event_id": kalshi_event.get("event_id"),
                    #"poly_market_id": poly_market.get("market_id"),
                    "kalshi_market_id": kalshi_market.get("market_id"),
                })

    df_matched_markets = pd.DataFrame(all_matched_data)
    df_event_summary = pd.DataFrame(event_match_summary)
    df_debug_no_markets = pd.DataFrame(debug_no_markets)

    print(f"\n{'='*80}")
    print(f"MATCHING COMPLETE")
    print(f"{'='*80}")

    print(f"\n📊 EVENT-LEVEL SUMMARY:")
    print(f"Total matched events: {len(df_event_summary)}")
    print(f"\nEvents by sport:")
    if len(df_event_summary) > 0:
        print(df_event_summary['sport'].value_counts())

    print(f"\n📊 MARKET-LEVEL SUMMARY:")
    print(f"Total matched markets: {len(df_matched_markets)}")
    if len(df_event_summary) > 0:
        print(f"Average markets per event: {len(df_matched_markets) / len(df_event_summary):.2f}")

    print(f"\n⚠️ DEBUG - EVENTS WITH NO MARKET MATCHES:")
    print(f"Total events with 0 markets matched: {len(df_debug_no_markets)}")
    if len(df_debug_no_markets) > 0:
        print(f"\nDistribution by sport:")
        print(df_debug_no_markets['sport'].value_counts())
        print(f"\nFirst 10 problematic events:")
        debug_cols = ['sport', 'poly_event', 'poly_event_slug', 'kalshi_event', 'sample_poly_question', 'sample_kalshi_title']
        print(df_debug_no_markets[debug_cols].head(10).to_string(index=False, max_colwidth=50))

    print(f"\n📈 MARKETS PER EVENT BREAKDOWN:")
    if len(df_matched_markets) > 0:
        markets_per_event = df_matched_markets.groupby(['poly_event_title', 'kalshi_event_title']).size()
        print(f"Events with 0 markets: {len(df_event_summary) - len(markets_per_event)}")
        print(f"Events with 1 market: {(markets_per_event == 1).sum()}")
        print(f"Events with 2 markets: {(markets_per_event == 2).sum()}")
        print(f"Events with 3+ markets: {(markets_per_event >= 3).sum()}")

    print("\n✅ FINAL DATASETS READY:")
    print("  - df_matched_markets: All matched markets with prices")
    print("  - df_event_summary: Summary of matched events")
    print("  - df_debug_no_markets: Events that failed market matching")

if __name__ == "__main__":
    main()