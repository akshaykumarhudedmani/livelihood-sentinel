import streamlit as st
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
import google.generativeai as genai
import os

st.set_page_config(page_title="News & Alerts", page_icon="📰", layout="wide")

# ==========================================
# 0. CONFIG & STREAM MAP
# ==========================================
STREAM_RSS_MAP = {
    "CSE / Tech": "https://www.sciencedaily.com/rss/computers_math/computer_science.xml",
    "Finance / Commerce": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Medical / Biology": "https://www.sciencedaily.com/rss/health_medicine.xml",
    "Arts / Humanities": "https://indianexpress.com/section/lifestyle/art-and-culture/feed/",
    "Law": "https://www.barandbench.com/route/feed.xml",
    "Architecture": "https://www.archdaily.com/feed/rss/",
    "Management (BBA/MBA)": "https://economictimes.indiatimes.com/small-biz/rssfeeds/5575607.cms",
    "General": "https://indianexpress.com/section/education/feed/"
}

# Motivation Quotes Map (Field Specific)
MOTIVATION_MAP = {
    "CSE / Tech": "“Talk is cheap. Show me the code.” – Linus Torvalds",
    "Finance / Commerce": "“Price is what you pay. Value is what you get.” – Warren Buffett",
    "Medical / Biology": "“Wherever the art of Medicine is loved, there is also a love of Humanity.”",
    "Arts / Humanities": "“Creativity takes courage.” – Henri Matisse",
    "Law": "“Justice cannot be for one side alone, but must be for both.”",
    "Architecture": "“We shape our buildings; thereafter they shape us.”",
    "Management (BBA/MBA)": "“Leadership is the capacity to translate vision into reality.”",
    "General": "“The expert in anything was once a beginner.”"
}

# ==========================================
# 1. AUTH & SECURITY
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("⚠️ Access Denied. Please login first.")
    st.stop()

# ==========================================
# 2. AI HELPER
# ==========================================
def ask_gemini_decrypt(headline):
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key: return "⚠️ API Key missing."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = f"Translate this news headline into 1 simple, urgent sentence for a common person: '{headline}'"
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Could not decrypt. Server busy."

@st.cache_data(ttl=600)
def fetch_rss(url, limit=3):
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
    except Exception:
        return []

# ==========================================
# 3. ROUTING LOGIC
# ==========================================
user_type = st.session_state.get("user_type", "Standard")
stream = st.session_state.get("study_stream", "General")

if user_type == "Student":
    st.title("📰 Campus & Career Radar")
    st.caption(f"Curated Intelligence for **{stream}** Students")
else:
    st.title("📰 Market & Livelihood Alerts")
    st.caption("Official RBI/SEBI Feeds • Personalized Risk Drills")

st.divider()

# ==========================================
# 4. LIVE NEWS FEED
# ==========================================
st.subheader("📡 Live Feed")
col1, col2 = st.columns(2)

with col1:
    if user_type == "Student":
        target_feed = STREAM_RSS_MAP.get(stream, STREAM_RSS_MAP["General"])
        st.markdown(f"**🎓 Industry Updates ({stream.split('/')[0]})**")
    else:
        target_feed = "https://www.rbi.org.in/pressreleases_rss.xml"
        st.markdown("**🏦 Economy & Policy (RBI)**")

    news_items = fetch_rss(target_feed, 3)
    if news_items:
        for i, item in enumerate(news_items):
            with st.container(border=True):
                st.markdown(f"[{item['title']}]({item['link']})")
                if st.button("✨ Decrypt", key=f"d1_{i}"):
                    with st.spinner(".."):
                        st.info(ask_gemini_decrypt(item['title']))
    else:
        st.caption("No live updates.")

with col2:
    if user_type == "Student":
        st.markdown("**🏫 General Education News**")
        sec_feed = STREAM_RSS_MAP["General"]
    else:
        st.markdown("**📈 Market Signals (SEBI)**")
        sec_feed = "https://www.sebi.gov.in/sebirss.xml"

    sec_items = fetch_rss(sec_feed, 3)
    if sec_items:
        for i, item in enumerate(sec_items):
            with st.container(border=True):
                st.markdown(f"[{item['title']}]({item['link']})")
                if st.button("✨ Decrypt", key=f"d2_{i}"):
                    with st.spinner(".."):
                        st.info(ask_gemini_decrypt(item['title']))
    else:
        st.caption("No live updates.")

st.divider()

# ==========================================
# 5. CARDS: MOTIVATION vs DRILLS
# ==========================================
if user_type == "Student":
    st.subheader("🚀 Daily Boost")
    st.caption("Fuel for your mind and wallet.")
    
    # 1. Motivation Card
    quote = MOTIVATION_MAP.get(stream, MOTIVATION_MAP["General"])
    
    # Object for Voice Engine
    motivation_obj = {
        "id": "daily_motivation",
        "title": f"Study Motivation ({stream.split('/')[0]})",
        "summary": quote,
        "desc": "Daily inspiration for your field."
    }

    with st.container(border=True):
        c_icon, c_info = st.columns([0.1, 0.9])
        with c_icon:
            st.markdown("## 🔥")
        with c_info:
            st.markdown(f"**{motivation_obj['title']}**")
            st.write(f"*{quote}*")
            st.caption("Keep pushing. You are building your future.")
            
            
            if st.button("🎙️ Listen", key="btn_voice_mot"):
                
                st.session_state.pop("voice_audio_mp3", None)
                st.session_state.pop("translated_script", None)
                st.session_state.pop("voice_script", None)
                
                
                st.session_state["voice_selected_alert_id"] = "daily_motivation"
                st.session_state["alerts"] = [motivation_obj] 
                st.switch_page("pages/voice.py")

    # 2. Financial Advice Card (Compassionate)
    advice_text = "Never be ashamed of not having money. It is a temporary stage, not your identity. Save what you can. If you really need to borrow, ask close friends or family—there is always someone willing to help."
    advice_obj = {
        "id": "financial_advice_note",
        "title": "Sentinel Advice: On Being Broke",
        "summary": advice_text,
        "desc": "Financial mental health check."
    }

    with st.container(border=True):
        c_icon, c_info = st.columns([0.1, 0.9])
        with c_icon:
            st.markdown("## 💚")
        with c_info:
            st.markdown(f"**{advice_obj['title']}**")
            st.write("Never be ashamed of not having money. It is a temporary stage, not your identity.")
            st.write("Save what you can. If you really need to borrow, ask close friends or family—there is always someone willing to help.")
            
            
            if st.button("🎙️ Listen", key="btn_voice_adv"):
                
                st.session_state.pop("voice_audio_mp3", None)
                st.session_state.pop("translated_script", None)
                st.session_state.pop("voice_script", None)
                
                
                st.session_state["voice_selected_alert_id"] = "financial_advice_note"
                st.session_state["alerts"] = [advice_obj]
                st.switch_page("pages/voice.py")

else:
    # --- STANDARD MODE: KEEPS DRILLS ---
    st.subheader("🚨 Threat Simulations")
    st.caption("Potential scenarios to test your resilience.")

    simulations = []
    crops = st.session_state.get("crops_grown", [])
    transport = int(st.session_state.get("transport", 0))
    emi_total = int(st.session_state.get("emi_total", 0))

    if transport > 0:
        simulations.append({
            "id": "fuel_drill", "icon": "⛽", "title": "Fuel Supply Shock",
            "desc": "Global oil prices spike by 15%.",
            "summary": f"Impact: Transport cost rises by ~₹{int(transport*0.15)}.", "level": "WARNING"
        })

    if emi_total > 0:
        simulations.append({
            "id": "rate_drill", "icon": "📉", "title": "Interest Rate Surge",
            "desc": "Repo rate raised by 50bps.",
            "summary": "Loan tenure might increase by 6-12 months.", "level": "CRITICAL"
        })

    if not simulations:
        simulations.append({
            "id": "inflation_drill", "icon": "🛒", "title": "Cost of Living Spike",
            "desc": "Vegetable prices double.",
            "summary": "Buying power reduced. Cut discretionary spend.", "level": "ADVISORY"
        })

    for sim in simulations:
        color_map = {"CRITICAL": "red", "WARNING": "orange", "ADVISORY": "blue"} 
        color = color_map.get(sim["level"], "gray")
        
        with st.container(border=True):
            c_icon, c_info = st.columns([0.1, 0.9])
            with c_icon:
                st.markdown(f"## {sim['icon']}")
            with c_info:
                st.markdown(f":{color}[**{sim['title']}**]")
                st.write(sim['summary'])
                
                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.button("🎙️ Listen", key=f"btn_voice_{sim['id']}", use_container_width=True):
                        
                        st.session_state.pop("voice_audio_mp3", None)
                        st.session_state.pop("translated_script", None)
                        st.session_state.pop("voice_script", None)

                        st.session_state["voice_selected_alert_id"] = sim["id"]
                        st.session_state["alerts"] = simulations
                        st.switch_page("pages/voice.py")
                with b2:
                     if st.button("💡 Protocol", key=f"btn_advice_{sim['id']}", use_container_width=True):
                         st.switch_page("pages/advice.py")