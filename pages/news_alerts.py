import streamlit as st
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
import google.generativeai as genai
import os

st.set_page_config(page_title="News & Alerts", page_icon="📰", layout="wide")

# ==========================================
# 0. AUTH & SECURITY
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Access Denied. Please login first.")
    st.stop()

# ==========================================
# 1. AI HELPER (Decrypt Only)
# ==========================================
def ask_gemini_decrypt(headline):
    """
    Translates boring official jargon into 1 simple sentence.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key: return "⚠️ API Key missing."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = f"Translate this news headline into 1 simple, urgent sentence for a common person: '{headline}'"
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Could not decrypt."

# ==========================================
# 2. PROFILE LOADING (Strict Input Gate)
# ==========================================
if not st.session_state.get("profile_complete", False):
    st.info("⚠️ Profile Missing. We cannot filter news without your financial inputs.")
    if st.button("Go to Tracking Setup"):
        st.switch_page("pages/tracking.py")
    st.stop()

# Load User Inputs
income = int(st.session_state.get("monthly_income", 0))
transport = int(st.session_state.get("transport", 0))
emi_total = int(st.session_state.get("emi_total", 0))
burn = int(st.session_state.get("burn", 0))
runway = int(st.session_state.get("runway_days", 0))
crops = st.session_state.get("crops_grown", [])
held_assets = st.session_state.get("held_assets", [])

# Determine User Type
is_investor = any(x in held_assets for x in ["Stocks / Mutual Funds", "Gold", "Crypto (BTC/ETH)"])
is_borrower = emi_total > 0
is_farmer = len(crops) > 0
is_commuter = transport > 0

st.title("📰 News & Alerts")
st.caption("Live official updates • Personalized simulation drills")
st.divider()

# ==========================================
# 3. REAL NEWS (Official Feeds)
# ==========================================
st.subheader("🏛️ Official Headlines (Live)")

@st.cache_data(ttl=600)
def fetch_rss(url, limit=2):
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())
        items = []
        for item in root.findall(".//item")[:limit]:
            title = item.findtext("title")
            link = item.findtext("link")
            if title: items.append({"title": title, "link": link})
        return items
    except:
        return []

# Layout Logic based on Input
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🏦 Economy & Banking (RBI)**")
    rbi_news = fetch_rss("https://www.rbi.org.in/pressreleases_rss.xml", 2)
    if rbi_news:
        for i, item in enumerate(rbi_news):
            with st.container(border=True):
                st.markdown(f"[{item['title']}]({item['link']})")
                # THE DECRYPT BUTTON
                k = f"dec_rbi_{i}"
                if st.button("✨ Decrypt", key=k, help="Translate legal jargon"):
                    with st.spinner(".."):
                        dec = ask_gemini_decrypt(item['title'])
                        st.info(dec)
    else:
        st.caption("No updates.")

with col2:
    if is_investor:
        st.markdown("**📈 Markets (SEBI)**")
        sebi_news = fetch_rss("https://www.sebi.gov.in/sebirss.xml", 2)
        if sebi_news:
            for i, item in enumerate(sebi_news):
                with st.container(border=True):
                    st.markdown(f"[{item['title']}]({item['link']})")
                    k = f"dec_sebi_{i}"
                    if st.button("✨ Decrypt", key=k):
                        with st.spinner(".."):
                            dec = ask_gemini_decrypt(item['title'])
                            st.info(dec)
    else:
        # If not investor, show something generic or empty
        st.markdown("**🌾 Agriculture (Agmarknet)**")
        st.caption("Market prices trending stable.")
        st.link_button("Open Mandi Prices", "https://agmarknet.gov.in")

st.divider()

# ==========================================
# 4. SIMULATION DRILLS (Strictly Input Based)
# ==========================================
st.subheader("🚨 Simulation Drills (Demo Only)")
st.caption("These are **GENERATED SCENARIOS** to test your financial resilience.")

simulations = []

# DRILL 1: FUEL HIKE (Only for Commuters)
if is_commuter:
    impact_amt = int(transport * 0.15)
    simulations.append({
        "id": "fuel_drill",
        "icon": "⛽",
        "title": "[SIMULATION] Fuel Supply Shock",
        "desc": "Global oil prices spike by 15%.",
        "summary": f"Global oil prices spike by 15%. Your transport costs increase by ₹{impact_amt}/month.",
        "level": "WARNING"
    })

# DRILL 2: INTEREST RATE HIKE (Only for Borrowers)
if is_borrower:
    emi_impact = int(emi_total * 0.05)
    simulations.append({
        "id": "rate_drill",
        "icon": "💸",
        "title": "[SIMULATION] Interest Rate Surge",
        "desc": "Central Bank raises repo rate by 50bps.",
        "summary": f"Central Bank raises repo rate by 50bps. Your loan EMIs may rise by ~₹{emi_impact}/month.",
        "level": "CRITICAL"
    })

# DRILL 3: WEATHER EVENT (Only for Farmers)
if is_farmer:
    crop_list = ", ".join(crops)
    simulations.append({
        "id": "weather_drill",
        "icon": "⛈️",
        "title": "[SIMULATION] Unseasonal Rainfall Alert",
        "desc": f"Heavy rains forecast in your district.",
        "summary": f"Heavy rains forecast. High risk of fungal infection for: {crop_list}.",
        "level": "CRITICAL"
    })

# DRILL 4: INFLATION (Everyone)
inflation_amt = int(income * 0.03)
simulations.append({
    "id": "inflation_drill",
    "icon": "🛒",
    "title": "[SIMULATION] Cost of Living Spike",
    "desc": "Food inflation hits 3-year high.",
    "summary": f"Food inflation hits 3-year high. Estimated buying power loss: ₹{inflation_amt}/month.",
    "level": "ADVISORY"
})

# --- SYNCHRONIZE WITH VOICE ENGINE ---
# We overwrite the session alerts so 'Voice' page can see these simulations
st.session_state["alerts"] = simulations

# --- RENDER SIMULATIONS ---
if not simulations:
    st.success("No active drills relevant to your profile.")

for sim in simulations:
    # Color coding
    color_map = {"CRITICAL": "red", "WARNING": "orange", "ADVISORY": "blue"} 
    color = color_map.get(sim["level"], "gray")
    
    with st.container(border=True):
        c_icon, c_info = st.columns([0.1, 0.9])
        
        with c_icon:
            st.markdown(f"## {sim['icon']}")
            
        with c_info:
            st.markdown(f":{color}[**{sim['title']}**]")
            st.write(sim['summary'])
            
            # VOICE BUTTON (Replaces AI Analysis)
            # This directly links to voice.py
            if st.button("🎙️ Listen to Briefing", key=f"btn_{sim['id']}"):
                st.session_state["voice_selected_alert_id"] = sim["id"]
                st.switch_page("pages/voice.py")