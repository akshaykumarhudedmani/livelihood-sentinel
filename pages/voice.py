import streamlit as st
from gtts import gTTS
from io import BytesIO
from deep_translator import GoogleTranslator
import requests
from streamlit_lottie import st_lottie
import time

st.set_page_config(
    page_title="Voice Assistant",
    page_icon="🎙️",
    layout="wide"
)

# ==========================================
# 1. SETUP & ASSETS
# ==========================================

# ---- Lottie Loader ----
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_voice = load_lottieurl("https://lottie.host/17158f55-1b4e-4df7-8326-9f880482592d/0F7e8eX4l4.json")

if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

# ==========================================
# 2. DATA PREP (The Fix)
# ==========================================
user_type = st.session_state.get("user_type", "Standard")

# --- CASE A: STUDENT MODE ---
if user_type == "Student":
    stream = st.session_state.get("study_stream", "General")
    
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
    
    quote = MOTIVATION_MAP.get(stream, MOTIVATION_MAP["General"])
    
    # Force Student Alerts
    st.session_state["alerts"] = [
        {
            "id": "daily_motivation",
            "title": f"Study Motivation ({stream.split('/')[0]})",
            "summary": quote,
            "desc": "Daily inspiration for your field."
        },
        {
            "id": "financial_advice_note",
            "title": "Sentinel Advice: On Being Broke",
            "summary": "Never be ashamed of not having money. It is a temporary stage, not your identity. Save what you can. If you really need to borrow, ask close friends or family—there is always someone willing to help.",
            "desc": "Financial mental health check."
        }
    ]

# --- CASE B: STANDARD MODE (The Fix) ---
else:
    # 1. Check if we accidentally have Student alerts loaded (clean up)
    current_alerts = st.session_state.get("alerts", [])
    if current_alerts and current_alerts[0]["id"] == "daily_motivation":
        current_alerts = [] # Wipe them
        
    # 2. If Empty, Generate Standard Drills on the spot
    if not current_alerts:
        transport = int(st.session_state.get("transport", 0))
        emi_total = int(st.session_state.get("emi_total", 0))
        
        standard_drills = []
        
        # Drill 1: Fuel
        if transport > 0:
            standard_drills.append({
                "id": "fuel_drill",
                "title": "Fuel Supply Shock",
                "summary": f"Global oil prices have spiked. Your estimated transport cost will rise by ₹{int(transport*0.15)}. Consider pooling or public transit.",
                "desc": "Impact Analysis: Moderate"
            })
            
        # Drill 2: Loans
        if emi_total > 0:
            standard_drills.append({
                "id": "rate_drill",
                "title": "Interest Rate Surge",
                "summary": "The Central Bank has raised rates. Your loan tenure may extend by 6-12 months. Pre-payment is advised if possible.",
                "desc": "Impact Analysis: Critical"
            })
            
        # Drill 3: Inflation (Default for everyone)
        standard_drills.append({
            "id": "inflation_drill",
            "title": "Cost of Living Report",
            "summary": "Vegetable and utility prices are trending up 8%. It is advised to cut discretionary spending this week to maintain your runway.",
            "desc": "General Advisory"
        })
        
        st.session_state["alerts"] = standard_drills

# ==========================================
# 3. UI & LOGIC
# ==========================================

# ---- Header Section ----
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🎙️ Sentinel Voice")
    if user_type == "Student":
        st.caption("Listen to your Daily Motivation or Financial Compass.")
    else:
        st.caption("Daily Briefing & Risk Simulation Audio.")

# ---- Language Selector ----
LANG_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Tamil": "ta",
    "Telugu": "te"
}
selected_lang_name = st.selectbox("Broadcast Language", list(LANG_MAP.keys()), index=0)
target_code = LANG_MAP[selected_lang_name]

st.divider()

# ==========================================
# 4. CONTENT SELECTION
# ==========================================
left_col, right_col = st.columns([1, 1])

# --- LEFT COLUMN: Controls ---
with left_col:
    alerts = st.session_state.get("alerts", [])
    
    if not alerts:
        st.info("No active briefings available.")
        if st.button("← Go to Dashboard"):
            st.switch_page("pages/home.py")
        st.stop()
    
    # Create valid list of IDs
    alert_ids = [a["id"] for a in alerts]
    alert_titles = [f"{'🔥' if 'motivation' in a['id'] else '📢'} {a['title']}" for a in alerts]
    
    # Determine default index
    default_idx = 0
    pre_selected_id = st.session_state.get("voice_selected_alert_id")
    if pre_selected_id in alert_ids:
        default_idx = alert_ids.index(pre_selected_id)

    # The Dropdown
    selected_idx = st.selectbox(
        "Select Content to Play:", 
        range(len(alerts)), 
        format_func=lambda x: alert_titles[x],
        index=default_idx
    )
    
    target_alert = alerts[selected_idx]
    
    # Detect Switch: If user changes dropdown, clear old audio to force regeneration
    if target_alert["id"] != st.session_state.get("current_voice_id_rendering"):
        st.session_state.pop("voice_audio_mp3", None)
        st.session_state["current_voice_id_rendering"] = target_alert["id"]
        # Update the session pointer
        st.session_state["voice_selected_alert_id"] = target_alert["id"]

    # ---- GENERATOR LOGIC ----
    
    # 1. Build Raw Script
    raw_script = f"Hello. Here is your briefing for: {target_alert['title']}. \n\n {target_alert['summary']} \n\n {target_alert.get('desc', '')}"
    
    # 2. Check if we have Audio in memory
    audio_data = st.session_state.get("voice_audio_mp3")
    
    if audio_data:
        st.success("✅ Audio Ready")
        st.audio(audio_data, format="audio/mp3", autoplay=True)
        
        if st.button("🔄 Regenerate / Change Language"):
            st.session_state.pop("voice_audio_mp3", None)
            st.rerun()
            
    else:
        st.info("Ready to synthesize.")
        if st.button("▶️ Generate Audio", type="primary", use_container_width=True):
            
            with st.status("Processing Neural Speech...", expanded=True) as status:
                
                # 1. Translation (if needed)
                if target_code != "en":
                    st.write(f"Translating to {selected_lang_name}...")
                    try:
                        final_text = GoogleTranslator(source='auto', target=target_code).translate(raw_script)
                    except:
                        final_text = raw_script
                        st.error("Translation failed, falling back to English.")
                else:
                    final_text = raw_script
                
                # Save text for display
                st.session_state["translated_script"] = final_text
                
                st.write("Synthesizing Audio...")
                time.sleep(0.5)
                
                # 2. TTS Generation
                try:
                    tts = gTTS(text=final_text, lang=target_code, slow=False)
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    
                    st.session_state["voice_audio_mp3"] = fp
                    status.update(label="Complete!", state="complete", expanded=False)
                    st.rerun()
                    
                except Exception as e:
                    status.update(label="Failed", state="error")
                    st.error(f"TTS Error: {e}")

# --- RIGHT COLUMN: Script Display ---
with right_col:
    with st.container(border=True):
        c_head, c_anim = st.columns([3, 1])
        with c_head:
            st.markdown(f"**Script Preview ({selected_lang_name})**")
        with c_anim:
            if lottie_voice:
                st_lottie(lottie_voice, height=40, key="wave_anim")

        # Show either the translated text (if generated) or raw text
        display_text = st.session_state.get("translated_script", raw_script)
        
        st.text_area(
            "script_display",
            value=display_text,
            height=300,
            disabled=True,
            label_visibility="collapsed"
        )