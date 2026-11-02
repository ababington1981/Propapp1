
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="NBA Prop +EV Calculator & v7 Engine",
    page_icon="🏀",
    layout="wide"
)

def american_to_decimal(american_odds):
    """Converts American odds to decimal odds."""
    if american_odds > 0:
        return (american_odds / 100.0) + 1.0
    else:
        return (100.0 / abs(american_odds)) + 1.0

def american_to_implied_prob(american_odds):
    """Converts American odds to raw implied probability."""
    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    else:
        abs_odds = abs(american_odds)
        return abs_odds / (abs_odds + 100.0)

# App UI Header
st.title("🏀 NBA Prop +EV & v7 Engine Workspace")
st.markdown("Evaluate player props using raw no-vig math paired with the structured **v7 5-Lens Prop Engine** methodology.")

st.divider()

# Layout: Two columns (Inputs on Left, Engine & Results on Right)
input_col, results_col = st.columns([1, 1.2], gap="large")

with input_col:
    st.subheader("⚙️ Prop & Market Configuration")
    
    player_name = st.text_input("Player Name", value="LeBron James")
    prop_type = st.selectbox("Prop Category", ["Points", "Rebounds", "Assists", "PRA", "3-Pointers Made", "Blocks/Steals"])
    
    st.markdown("---")
    st.markdown("**1. Market No-Vig Odds**")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        odds_over = st.number_input("Market Over Odds", value=-112, step=1)
    with col_m2:
        odds_under = st.number_input("Market Under Odds", value=-108, step=1)

    st.markdown("**2. Your Bet Details**")
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        bet_side = st.selectbox("Side", ["Over", "Under"])
    with col_b2:
        offered_odds = st.number_input("Offered Odds", value=-110, step=1)
    with col_b3:
        stake = st.number_input("Stake ($)", value=100.0, step=10.0, min_value=1.0)

    st.markdown("---")
    st.subheader("🔍 v7 Engine Contextual Checkpoints")
    fatigue_factor = st.selectbox("Schedule / Fatigue Split", ["Normal Rest (2+ days)", "Standard B2B (Back-to-Back)", "3-in-4 / 4-in-5 Heavy Fatigue"])
    rotation_role = st.selectbox("Rotation & On/Off Unit Role", ["Starter (Standard Minutes)", "Usage Boost (Key Teammate Out)", "Bench / Secondary Unit Stagger"])
    blowout_risk = st.selectbox("Blowout / Garbage Time Risk", ["Low / Competitive Game", "Moderate Spread Disparity", "High Blowout / Bench Risk"])

# --- Calculations ---
raw_prob_over = american_to_implied_prob(odds_over)
raw_prob_under = american_to_implied_prob(odds_under)

total_implied_prob = raw_prob_over + raw_prob_under
vig_percentage = (total_implied_prob - 1.0) * 100

fair_prob_over = raw_prob_over / total_implied_prob
fair_prob_under = raw_prob_under / total_implied_prob
fair_prob = fair_prob_over if bet_side == "Over" else fair_prob_under

decimal_offered = american_to_decimal(offered_odds)
potential_payout = stake * decimal_offered
expected_value = (fair_prob * potential_payout) - stake
roi_percentage = (expected_value / stake) * 100

with results_col:
    st.subheader(f"📊 Analysis Results: {player_name} ({prop_type})")
    
    res_c1, res_c2, res_c3 = st.columns(3)
    res_c1.metric(f"No-Vig Fair Prob ({bet_side})", f"{fair_prob * 100:.2f}%")
    res_c2.metric("Market Vig (Overround)", f"{vig_percentage:.2f}%", delta_color="inverse")
    
    ev_label = "Positive +EV 🟢" if expected_value > 0 else "Negative -EV 🔴"
    res_c3.metric("Expected Value ($EV)", f"${expected_value:.2f}", delta=ev_label)

    st.markdown(f"**Expected ROI:** `{roi_percentage:.2f}%` on a `${stake:.2f}` stake via offered odds (`{offered_odds:+d}`).")
    
    st.markdown("---")
    st.subheader("🧠 v7 5-Lens Engine Evaluation")
    
    # Dynamic engine insights based on user selections
    lens_1_note = "✅ Clean rest baseline." if fatigue_factor == "Normal Rest (2+ days)" else "⚠️ Fatigue Tax Applied: Back-to-back or dense schedule detected; haircut late-game legs."
    lens_2_note = "📈 Starter baseline usage active." if rotation_role == "Starter (Standard Minutes)" else "🔥 Usage Spike: Teammate absence or bench stagger triggers elevated volume potential."
    lens_4_note = "🛡️ Stable rotation floor." if blowout_risk == "Low / Competitive Game" else "⚠️ Blowout Risk: Consult coach garbage-time tendencies; monitor minute volatility."

    st.info(f"""
    * **🩹 Lens 1 & 2 (Fatigue & Roster):** {lens_1_note} {lens_2_note}
    * **📉 Lens 4 (Devil's Advocate & Blowout):** {lens_4_note}
    * **🪙 Lens 5 (Market Edge):** True no-vig probability is **{fair_prob * 100:.2f}%**. 
    """)
    
    if expected_value > 0:
        st.success(f"🎯 **Verdict:** **TAKE ({bet_side.upper()})** — Mathematically +EV line identified. Recommended Unit Sizing: **1.0 Unit**.")
        if bet_side == "Over":
            st.markdown("💡 *v7 Ceiling Escalator Tip:* Consider laddering alternative milestone lines (e.g., 2+, 3+) for plus-money ceiling payouts if usage metrics support a blowout performance.")
    else:
        st.warning("🛑 **Verdict:** **PASS / UNDER LEAN** — Line lacks positive expected value based on current sharp market pricing.")

# Footer details expander
with st.expander("View Underlying Math & Metrics"):
    st.write(f"- **Raw Over Implied Prob:** `{raw_prob_over * 100:.2f}%`")
    st.write(f"- **Raw Under Implied Prob:** `{raw_prob_under * 100:.2f}%`")
    st.write(f"- **Offered Decimal Odds:** `{decimal_offered:.3f}`")
    st.write(f"- **Total Return Potential:** `${potential_payout:.2f}`")
