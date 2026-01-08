import streamlit as st
import time
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

# --- PATH-SAFE LOGO LOADER ---
# This ensures the cloud finds 'hero.jpeg' inside the 'assets' folder
LOGO_PATH = os.path.join(os.getcwd(), "assets", "hero.jpeg")

def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.warning(f"⚠️ hero.jpeg missing in /assets/")

# ==========================================
# 0. AUTH CHECK
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

# ==========================================
# STATE 1: NEW USER (Profile Not Setup)
# ==========================================
if not st.session_state.get("profile_complete", False):
    st.title("Welcome to Livelihood Sentinel")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("### Let's secure your future.")
        st.write(
            "To activate your **Financial Immune System**, we need to know your "
            "survival baseline (Income, Expenses, Assets)."
        )
        st.info("It takes 30 seconds to setup your profile.")
        
        if st.button("🚀 Start Tracking Setup", type="primary", use_container_width=True):
            st.switch_page("pages/tracking.py")

    with c2:
        show_logo()
    
    st.stop()

# ==========================================
# STATE 2: ACTIVE DASHBOARD (Profile Done)
# ==========================================

# --- Logic: Risk Assessment ---
risk = int(st.session_state.get("risk_score", 0))
runway = int(st.session_state.get("runway_days", 0))

if risk >= 75 or runway <= 15:
    status_msg = "CRITICAL THREATS DETECTED"
    status_color = "red"
elif risk >= 50 or runway <= 30:
    status_msg = "MONITORING RISKS"
    status_color = "orange"
else:
    status_msg = "LIVELIHOOD SECURE"
    status_color = "green"

# --- Dashboard Header ---
c1, c2 = st.columns([2, 1])

with c1:
    st.title("Livelihood Sentinel")
    st.caption(f"Language: {st.session_state.get('lang', 'English')}")
    
    st.markdown(f"### Status: :{status_color}[{status_msg}]")
    st.write("Your **Financial Immune System** is active.")
    
    if st.button("🔍 Run Deep Scan", help="Analyze new alerts"):
        with st.status("📡 Initializing Sentinel Scan...", expanded=True) as status:
            st.write("Connecting to SEBI/RBI satellite feeds...")
            time.sleep(0.8)
            st.write("Filtering noise & irrelevant headlines...")
            time.sleep(0.8)
            st.write("Applying Gemini Risk Models...")
            time.sleep(0.8)
            status.update(label="Scan Complete! Redirecting...", state="complete", expanded=False)
            time.sleep(0.5)
            st.switch_page("pages/news_alerts.py")

with c2:
    show_logo()

st.divider()

# --- The Metrics ---
income = int(st.session_state.get("monthly_income", 0))
burn = int(st.session_state.get("burn", 0))
net_savings = int(st.session_state.get("net_savings", 0))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Monthly Income", f"₹{income:,}")
col2.metric("Monthly Burn", f"₹{burn:,}")
col3.metric("Net Savings", f"₹{net_savings:,}")

# Infinite runway handling
if runway > 900:
    runway_display = "Infinite"
    delta_display = "Safe"
else:
    runway_display = f"{runway} Days"
    delta_display = "-2 days" if runway < 30 else "Stable"

col4.metric(
    "Survival Runway", 
    runway_display, 
    delta=delta_display, 
    delta_color="inverse"
)

# --- Gemini Section ---
st.divider()
st.subheader("🤖 Gemini Analysis")

with st.container(border=True):
    if risk > 50:
        st.markdown(f"**Gemini Insight:** High burn rate detected (₹{burn:,}). "
                    "Action: Check 'Variable' expenses in Tracking.")
    elif runway > 900:
        st.markdown("**Gemini Insight:** You are financially secure. "
                    "Recommendation: Consider investing surplus cash into high-yield assets.")
    else:
        st.markdown("**Gemini Insight:** Financial health is stable. "
                    "Recommendation: Build an emergency buffer for crop seasonality.")
    
    st.caption("Powered by Gemini 1.5 Flash • Real-time Calculation")

# --- Footer Navigation ---
left, right = st.columns(2)
with left:
    with st.container(border=True):
        st.write("⚠️ **Threat Preview**")
        st.caption("Active Alerts")
        if st.button("View News & Alerts", key="nav_news", use_container_width=True):
            st.switch_page("pages/news_alerts.py")

with right:
    with st.container(border=True):
        st.write("🎙️ **Daily Briefing**")
        st.caption("Audio Update")
        if st.button("Open Voice Assistant", key="nav_voice", use_container_width=True):
            st.switch_page("pages/voice.py")