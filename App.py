import time
import requests
from flask import Flask, jsonify, request
from typing import Dict, List, Any, Optional

app = Flask(__name__)

# Simple in-memory cache to avoid burning API limits on repeated custom tab selections
CACHE_TTL = 60  # seconds
odds_cache = {}

class LivePropOddsEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports"

    def fetch_player_prop_odds(self, sport_key: str, event_id: str, market_type: str = "player_points") -> Optional[Dict[str, Any]]:
        """Fetches live player prop odds from the provider API with caching."""
        cache_key = f"{sport_key}_{event_id}_{market_type}"
        current_time = time.time()

        if cache_key in odds_cache:
            cached_data, timestamp = odds_cache[cache_key]
            if current_time - timestamp < CACHE_TTL:
                print(f"[Cache Hit] Returning cached odds for {cache_key}")
                return cached_data

        url = f"{self.base_url}/{sport_key}/events/{event_id}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": "us",
            "markets": market_type,
            "oddsFormat": "american"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            odds_cache[cache_key] = (data, current_time)
            
            remaining = response.headers.get("x-requests-remaining")
            print(f"[API Info] Remaining API Requests: {remaining}")
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"[Error] Failed to fetch live prop odds: {e}")
            return None

    def parse_and_find_best_prices(self, bookmakers: List[Dict[str, Any]], target_player_name: str, market_key: str) -> Dict[str, Any]:
        """
        Parses bookmaker payloads, extracts lines/prices for a target player,
        and automatically identifies the best available odds for Over and Under.
        """
        matched_lines = []
        best_over = {"price": -99999, "sportsbook": None, "point": None}
        best_under = {"price": -99999, "sportsbook": None, "point": None}

        for bookmaker in bookmakers:
            markets = bookmaker.get("markets", [])
            market = next((m for m in markets if m.get("key") == market_key), None)
            
            if market:
                player_outcomes = [
                    outcome for outcome in market.get("outcomes", [])
                    if outcome.get("description") == target_player_name
                ]
                
                if player_outcomes:
                    bookmaker_title = bookmaker.get("title")
                    matched_lines.append({
                        "sportsbook": bookmaker_title,
                        "last_update": market.get("last_update"),
                        "outcomes": player_outcomes
                    })

                    # Evaluate best price/line shopping
                    for outcome in player_outcomes:
                        name = outcome.get("name", "").lower() # 'Over' or 'Under'
                        price = outcome.get("price")
                        point = outcome.get("point")

                        if "over" in name:
                            if best_over["price"] == -99999 or price > best_over["price"]:
                                best_over = {"price": price, "sportsbook": bookmaker_title, "point": point}
                        elif "under" in name:
                            if best_under["price"] == -99999 or price > best_under["price"]:
                                best_under = {"price": price, "sportsbook": bookmaker_title, "point": point}

        return {
            "all_sportsbook_lines": matched_lines,
            "best_odds": {
                "over": best_over if best_over["price"] != -99999 else None,
                "under": best_under if best_under["price"] != -99999 else None
            }
        }

    def handle_custom_tab_selection(self, sport_key: str, event_id: str, player_name: str, market_type: str) -> Dict[str, Any]:
        raw_data = self.fetch_player_prop_odds(sport_key, event_id, market_type)
        
        if not raw_data or "bookmakers" not in raw_data:
            return {"status": "error", "message": "No live odds data available for this fixture."}

        parsed_results = self.parse_and_find_best_prices(raw_data["bookmakers"], player_name, market_type)

        return {
            "status": "success",
            "player": player_name,
            "market": market_type,
            "fixture_id": event_id,
            "live_lines": parsed_results["all_sportsbook_lines"],
            "best_value": parsed_results["best_odds"]
        }

# Initialize engine (Replace with environment variable or your actual key in production)
prop_engine = LivePropOddsEngine(api_key="YOUR_API_KEY_HERE")

# ==========================================
# Flask API Endpoint for the Custom Tab UI
# ==========================================
@app.route("/api/custom-tab/player-odds", methods=["GET"])
def get_custom_player_odds():
    sport_key = request.args.get("sport", "basketball_nba")
    event_id = request.args.get("eventId")
    player_name = request.args.get("player")
    market_type = request.args.get("market", "player_points")

    if not event_id or not player_name:
        return jsonify({"status": "error", "message": "Missing required parameters: eventId and player"}), 400

    result = prop_engine.handle_custom_tab_selection(sport_key, event_id, player_name, market_type)
    return jsonify(result)

if __name__ == "__main__":
    print("Starting Live Prop Odds Backend for Custom Tab...")
    app.run(debug=True, port=5000)
