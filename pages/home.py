import streamlit as st
import time
import os
import google.generativeai as genai
from google.api_core import exceptions

# --- PAGE CONFIG ---
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# --- ASSET LOADER ---
LOGO_PATH = os.path.join(os.getcwd(), "assets", "hero.jpeg")

def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)

# ==========================================
# 0. AUTH & SECURITY GATE
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Access Denied. Please login first.")
    st.stop()

# ==========================================
# 1. AI ANALYSIS ENGINE (Professional Tone)
# ==========================================
def get_professional_insight(burn, runway, risk, income):
    """
    Asks Gemini for a structured professional assessment.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')

        # Professional Prompt
        prompt = (
            f"Act as a personal financial advisor. Status: "
            f"Burn: {burn}, Income: {income}, Runway: {runway} days, Risk Score: {risk}/100. "
            f"Generate a 3-line assessment:\n"
            f"RISK: [Identify the main financial risk. Max 10 words]\n"
            f"IMPACT: [What is the consequence? Max 10 words]\n"
            f"ACTION: [One specific recommendation. Max 10 words]\n"
            f"Do not use markdown. Just plain text lines."
        )

        # Retry Logic
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except exceptions.ResourceExhausted:
                time.sleep(2)
                continue
            except Exception:
                return None
        
        return None

    except Exception:
        return None

# ==========================================
# 2. STATE 1: INITIALIZATION (New User)
# ==========================================
if not st.session_state.get("profile_complete", False):
    st.title("Welcome to Livelihood Sentinel")
    st.markdown("### Step 1: Profile Setup")
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.write("To provide accurate risk alerts, we need to establish your financial baseline.")
        st.write("Please configure your **Income, Expenses & Assets** to activate the dashboard.")
        
        st.info("⏱️ Time required: ~45 seconds")
        
        st.write("")
        if st.button("▶️ Start Configuration", type="primary", use_container_width=True):
            st.switch_page("pages/tracking.py")

    with c2:
        show_logo()
        
    st.stop()

# ==========================================
# 3. STATE 2: MAIN DASHBOARD (Active)
# ==========================================

# --- LOAD METRICS ---
income = int(st.session_state.get("monthly_income", 0))
burn = int(st.session_state.get("burn", 0))
runway = int(st.session_state.get("runway_days", 0))
risk = int(st.session_state.get("risk_score", 0))

# --- HEADER SECTION ---
c1, c2 = st.columns([0.85, 0.15])
with c1:
    st.title("Financial Dashboard")
    st.caption(f"Status: Active | User: Demo | Risk Score: {risk}/100")
with c2:
    if st.button("🔄 Refresh"):
        st.rerun()

st.divider()

# ==========================================
# 4. COMPONENT: RUNWAY STATUS (Visual Bar)
# ==========================================
# Logic: Map 0-180 days to 0-100% progress
runway_cap = 180
progress_val = min(1.0, max(0.0, runway / runway_cap))

# Color Logic for text
if runway <= 30:
    gauge_msg = "CRITICAL LOW"
elif runway <= 90:
    gauge_msg = "NEEDS ATTENTION"
else:
    gauge_msg = "HEALTHY"

st.subheader("⏳ Survival Runway")
st.progress(progress_val, text=f"Runway Remaining: {runway} Days ({gauge_msg})")

if runway > 365:
    st.caption("✅ You have over 1 year of reserves. Long-term security achieved.")
elif runway < 30:
    st.caption("🚨 **Action Required:** Your savings will be depleted in less than 30 days.")

st.write("")

# ==========================================
# 5. COMPONENT: AI RISK ASSESSMENT (The Core)
# ==========================================
st.subheader("🧠 AI Risk Assessment")

# Check/Load AI Insight
if "hero_sitrep" not in st.session_state:
    st.session_state["hero_sitrep"] = None

# Layout
sit_col1, sit_col2 = st.columns([3, 1])

with sit_col1:
    container = st.container(border=True)
    
    if st.session_state["hero_sitrep"]:
        # Parse the 3 lines (RISK / IMPACT / ACTION)
        lines = st.session_state["hero_sitrep"].split('\n')
        risk_txt = "Analyzing..."
        impact_txt = "Calculating..."
        action_txt = "Standby..."
        
        for line in lines:
            if "RISK:" in line: risk_txt = line.replace("RISK:", "").strip()
            if "IMPACT:" in line: impact_txt = line.replace("IMPACT:", "").strip()
            if "ACTION:" in line: action_txt = line.replace("ACTION:", "").strip()
            
        # UI DISPLAY
        container.markdown(f"**⚠️ RISK:** {risk_txt}")
        container.markdown(f"**📉 IMPACT:** {impact_txt}")
        container.markdown(f"**✅ ACTION:** :green-background[{action_txt}]")
        
    else:
        container.info("Ready to analyze your latest financial data.")
        container.caption("Click 'Run Analysis' to generate a risk report.")

with sit_col2:
    # Large Action Button
    st.write("")
    if st.button("⚡ Run Analysis", type="primary", use_container_width=True):
        with st.spinner("Processing financial data..."):
            time.sleep(0.5)
            sitrep = get_professional_insight(burn, runway, risk, income)
            if sitrep:
                st.session_state["hero_sitrep"] = sitrep
            else:
                st.session_state["hero_sitrep"] = (
                    "RISK: Connection unstable.\n"
                    "IMPACT: Cannot calculate real-time risk.\n"
                    "ACTION: Please retry analysis."
                )
        st.rerun()

st.divider()

# ==========================================
# 6. COMPONENT: CASHFLOW ANALYSIS
# ==========================================
st.subheader("📊 Cashflow Analysis")

# Ratio of Burn vs Income
ratio = (burn / income) * 100 if income > 0 else 100
ratio = min(ratio, 100) # Cap at 100 for display

cf_c1, cf_c2, cf_c3 = st.columns([1, 4, 1])

with cf_c1:
    st.metric("Total Income", f"₹{income:,}", delta="Monthly Inflow")

with cf_c2:
    # The Visual Bar
    st.write("")
    st.write("")
    st.progress(ratio / 100, text=f"Burn Rate: {int(ratio)}% of Income")
    
    if burn > income:
        st.error(f"⚠️ DEFICIT: Spending exceeds income by ₹{burn - income:,}")
    else:
        st.success(f"✅ SURPLUS: Saving ₹{income - burn:,} / month")

with cf_c3:
    st.metric("Total Expenses", f"₹{burn:,}", delta="- Monthly Outflow", delta_color="inverse")

st.divider()

# ==========================================
# 7. NAVIGATION
# ==========================================
nav_c1, nav_c2 = st.columns(2)

with nav_c1:
    with st.container(border=True):
        st.subheader("📡 News & Alerts")
        alerts_count = len(st.session_state.get("alerts", []))
        if alerts_count > 0:
            st.markdown(f":red[**{alerts_count} Active Alerts**]")
        else:
            st.markdown(":green[**No immediate threats**]")
            
        if st.button("View Details ->", use_container_width=True):
            st.switch_page("pages/news_alerts.py")

with nav_c2:
    with st.container(border=True):
        st.subheader("💡 Advice & Protocols")
        st.markdown("Get tailored financial steps.")
        if st.button("Open Advice Console ->", use_container_width=True):
            st.switch_page("pages/advice.py")