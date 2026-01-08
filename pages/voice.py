import streamlit as st
from gtts import gTTS
from io import BytesIO
from deep_translator import GoogleTranslator
import requests
from streamlit_lottie import st_lottie
import time  # <--- NEW: Required for the loading effect

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

# Load "Sound Wave" Animation
lottie_voice = load_lottieurl("https://lottie.host/17158f55-1b4e-4df7-8326-9f880482592d/0F7e8eX4l4.json")

# ---- Auth gate ----
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

# ---- Header Section (Clean) ----
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🎙️ Sentinel Briefing")
    st.caption("Your personalized financial news anchor.")
    
st.divider()

# ---- Profile gate ----
if not st.session_state.get("profile_complete", False):
    st.info("Setup your tracking profile first to get voice updates.")
    if st.button("Go to Tracking"):
        st.switch_page("pages/tracking.py")
    st.stop()

# ==========================================
# 2. DATA PREP
# ==========================================
alerts = st.session_state.get("alerts", [])
resolved = st.session_state.get("resolved_alert_ids", set())

emi_total = int(st.session_state.get("emi_total", 0))
runway_days = int(st.session_state.get("runway_days", 0))

# Filter active alerts
active_alerts = [a for a in alerts if a.get("id") and a.get("id") not in resolved]
severity_rank = {"CRITICAL": 0, "WARNING": 1, "ADVISORY": 2}
active_alerts = sorted(
    active_alerts,
    key=lambda a: severity_rank.get(a.get("level", "ADVISORY"), 9),
)

# ---- Logic: Build Script ----
def build_voice_script(alert: dict) -> str:
    level = alert.get("level", "ADVISORY")
    title = alert.get("title", "Alert")
    summary = alert.get("summary", "")
    actions = (alert.get("actions") or [])[:2]

    tag_bits = []
    if runway_days: tag_bits.append(f"runway {runway_days} days")
    
    tag_line = ("Your context: " + ", ".join(tag_bits) + ".") if tag_bits else ""

    severity_line = {
        "CRITICAL": "Urgent attention required.",
        "WARNING": "This is a warning update.",
        "ADVISORY": "Here is an advisory update.",
    }.get(level, "Update.")

    lines = [
        "Welcome to your Livelihood Sentinel briefing.",
        severity_line,
        f"{title}.",
        summary,
        tag_line,
    ]
    
    if actions:
        lines.append("My recommended action is:")
        lines.append(actions[0])

    lines.append("This concludes your update.")
    return "\n\n".join(lines)

# ==========================================
# 3. HELPER FUNCTIONS (Safe & Cached)
# ==========================================

# 1. Cache the translation
@st.cache_data(show_spinner=False)
def safe_translate(text: str, target_lang: str) -> str:
    if target_lang == "en": 
        return text
    
    # Retry logic
    for attempt in range(3):
        try:
            return GoogleTranslator(source='auto', target=target_lang).translate(text)
        except Exception:
            time.sleep(1)
            
    return text # Fallback

# 2. Cache the audio generation
@st.cache_data(show_spinner=False)
def safe_synthesize_mp3(text: str, language_code: str) -> bytes:
    if not text.strip(): return None
    
    # Retry logic for gTTS
    for attempt in range(3):
        try:
            tts = gTTS(text=text, lang=language_code, slow=False)
            fp = BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
        except Exception:
            time.sleep(1.5)
            
    return None

# ==========================================
# 4. UI LAYOUT
# ==========================================
left_col, right_col = st.columns([1, 1.2])

# --- LEFT COLUMN: Controls ---
with left_col:
    st.subheader("1. Select Topic")
    
    if not active_alerts:
        st.success("No active threats. You are safe!")
        st.stop()

    current_selection_id = st.session_state.get("voice_selected_alert_id")
    
    alert_titles = [f"{a.get('level')} • {a.get('title')}" for a in active_alerts]
    default_idx = 0
    
    if current_selection_id:
        for i, a in enumerate(active_alerts):
            if a["id"] == current_selection_id:
                default_idx = i
                break

    chosen_idx = st.selectbox(
        "Choose alert to play:",
        range(len(alert_titles)),
        format_func=lambda x: alert_titles[x],
        index=default_idx
    )
    
    chosen_alert = active_alerts[chosen_idx]
    raw_script = build_voice_script(chosen_alert)

    st.write("")
    st.subheader("2. Language Settings")
    
    lang_map = {
        "English (Default)": "en",
        "Hindi (हिंदी)": "hi",
        "Kannada (ಕನ್ನಡ)": "kn",
        "Telugu (తెలుగు)": "te",
        "Tamil (தமிழ்)": "ta"
    }
    
    selected_lang_name = st.selectbox("Broadcast Language", list(lang_map.keys()))
    target_code = lang_map[selected_lang_name]

    st.write("")
    
    # --- UPGRADED BUTTON WITH LOADING ---
    if st.button("▶️ PLAY BRIEFING", type="primary", use_container_width=True):
        st.session_state["voice_audio_mp3"] = None
        
        # The Loading Sequence
        with st.status(f"🎙️ Generating {selected_lang_name} Audio...", expanded=True) as status:
            
            st.write("Fetching latest context from Firestore...")
            time.sleep(0.5)
            
            st.write(f"Translating script to {selected_lang_name}...")
            # 1. Translate (Safe)
            final_text = safe_translate(raw_script, target_code)
            st.session_state["translated_script"] = final_text
            time.sleep(0.5) 
            
            st.write("Synthesizing neural speech (Google TTS)...")
            # 2. Audio (Safe)
            mp3 = safe_synthesize_mp3(final_text, target_code)
            
            if mp3:
                st.session_state["voice_audio_mp3"] = mp3
                status.update(label="Audio Ready!", state="complete", expanded=False)
                st.rerun()
            else:
                status.update(label="Generation Failed", state="error")
                st.error("Server is busy. Please try again.")

    if st.button("← Back to Dashboard", use_container_width=True):
        st.switch_page("pages/home.py")

# --- RIGHT COLUMN: Display ---
with right_col:
    with st.container(border=True):
        head_c1, head_c2 = st.columns([3, 1])
        with head_c1:
            st.markdown(f"**Script Preview ({selected_lang_name})**")
        with head_c2:
            if lottie_voice:
                st_lottie(lottie_voice, height=40, key="wave_anim")

        display_text = st.session_state.get("translated_script", raw_script)
        
        st.text_area(
            "script_display",
            value=display_text,
            height=300,
            disabled=True,
            label_visibility="collapsed"
        )
        
        if st.session_state.get("voice_audio_mp3"):
            st.audio(st.session_state["voice_audio_mp3"], format="audio/mpeg", autoplay=True)
            st.success(f"Playing in {selected_lang_name}...")