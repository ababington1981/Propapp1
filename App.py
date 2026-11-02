import streamlit as st
import requests
from typing import Dict, List, Any, Optional

st.set_page_config(page_title="Custom Tab - Live Prop Odds", layout="wide")

class LivePropOddsEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports"

    # Use Streamlit's built-in caching to prevent burning your API limit
    @st.cache_data(ttl=60)
    def fetch_player_prop_odds(_self, sport_key: str, event_id: str, market_type: str) -> Optional[Dict[str, Any]]:
        url = f"{_self.base_url}/{sport_key}/events/{event_id}/odds"
        params = {
            "apiKey": _self.api_key,
            "regions": "us",
            "markets": market_type,
            "oddsFormat": "american"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch live prop odds: {e}")
            return None

    def parse_and_find_best_prices(self, bookmakers: List[Dict[str, Any]], target_player_name: str, market_key: str) -> Dict[str, Any]:
        matched_lines = []
        best_over = {"price": -99999, "sportsbook": None, "point": None}
        best_under = {"price": -99999, "sportsbook": None, "point": None}

        for bookmaker in bookmakers:
            markets = bookmaker.get("markets", [])
            market = next((m for m in markets if m.get("key") == market_key), None)
            
            if market:
                player_outcomes = [
                    outcome for outcome in market.get("outcomes", [])
                    if outcome.get("description") and target_player_name.lower() in outcome.get("description").lower()
                ]
                
                if player_outcomes:
                    bookmaker_title = bookmaker.get("title")
                    matched_lines.append({
                        "sportsbook": bookmaker_title,
                        "last_update": market.get("last_update"),
                        "outcomes": player_outcomes
                    })

                    for outcome in player_outcomes:
                        name = outcome.get("name", "").lower()
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

# ==========================================
# Streamlit UI Layout
# ==========================================
st.title("🏀 Custom Tab — Live Prop Odds")
st.write("Select your game, player, and market to check real-time sportsbook lines and best value odds.")

# Sidebar Configuration
api_key = st.sidebar.text_input("The Odds API Key", type="password", value="")

if not api_key:
    st.warning("⚠️ Please enter your Odds API key in the sidebar to load live odds.")
else:
    engine = LivePropOddsEngine(api_key=api_key)

    col1, col2 = st.columns(2)
    with col1:
        sport_key = st.selectbox("Sport", ["basketball_nba", "americanfootball_nfl", "icehockey_nhl"])
        market_type = st.selectbox("Market", ["player_points", "player_rebounds", "player_assists", "player_pass_yds"])
    with col2:
        event_id = st.text_input("Event ID", value="2b9d3b5b63d902315228a47881ef1d65")
        player_name = st.text_input("Player Name", value="LeBron James")

    if st.button("Fetch Live Prop Odds", type="primary"):
        with st.spinner("Fetching live odds from sportsbooks..."):
            raw_data = engine.fetch_player_prop_odds(sport_key, event_id, market_type)

            if raw_data and "bookmakers" in raw_data:
                results = engine.parse_and_find_best_prices(raw_data["bookmakers"], player_name, market_type)
                
                st.success(f"Successfully loaded lines for {player_name}!")

                # Display Best Value Section
                st.subheader("🔥 Best Available Odds")
                best_cols = st.columns(2)
                best_odds = results["best_odds"]
                
                with best_cols[0]:
                    if best_odds["over"]:
                        bo = best_odds["over"]
                        st.metric(label="Best Over Price", value=f"{bo['price']:+d}", delta=f"{bo['sportsbook']} ({bo['point']} pts)")
                    else:
                        st.info("No Over line found.")

                with best_cols[1]:
                    if best_odds["under"]:
                        bu = best_odds["under"]
                        st.metric(label="Best Under Price", value=f"{bu['price']:+d}", delta=f"{bu['sportsbook']} ({bu['point']} pts)")
                    else:
                        st.info("No Under line found.")

                # Display All Sportsbook Lines
                st.subheader("📊 All Sportsbook Lines")
                if results["all_sportsbook_lines"]:
                    for bookie in results["all_sportsbook_lines"]:
                        with st.expander(f"{bookie['sportsbook']}"):
                            for outcome in bookie["outcomes"]:
                                st.write(f"**{outcome.get('name')}** | Line: {outcome.get('point')} | Odds: {outcome.get('price')}")
                else:
                    st.warning("No matching sportsbook lines found for this player in this event.")
            else:
                st.error("Could not fetch data. Verify your Event ID and ensure your API key is valid.")
