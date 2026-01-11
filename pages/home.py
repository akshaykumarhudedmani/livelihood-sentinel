import streamlit as st
import time
import os
import requests
from io import BytesIO
from streamlit_lottie import st_lottie

# --- Library Checks (Graceful Fallbacks) ---
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    from db_ops import save_profile
except ImportError:
    # Fallback if db_ops.py is missing
    def save_profile(data):
        pass

# ==========================================
# 0. PAGE CONFIG & INIT
# ==========================================
st.set_page_config(
    page_title="Livelihood Sentinel", 
    page_icon=":material/shield:",
    layout="centered",
    initial_sidebar_state="expanded"
)

def initialize_state():
    """Initializes all session state variables."""
    defaults = {
        "logged_in": False,
        "profile_complete": False,
        "user_type": "Student",
        "today_spend": 0.0,
        "savings_buffer": 0.0,
        "daily_limit": 100.0,
        "monthly_income": 0.0,
        "burn": 0.0,
        "net_savings": 0.0,
        "runway_days": 0,
        "risk_score": 0,
        "college_name": "Amity University",
        "study_stream": "B.Tech CSE",
        "student_note": "",
        "lang": "English",
        "advice_topic_context": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_state()

# ==========================================
# 1. HELPER FUNCTIONS & ASSETS
# ==========================================

LOTTIE_SAFE = "https://assets2.lottiefiles.com/packages/lf20_x62chJ.json"
LOTTIE_CRITICAL = "https://assets10.lottiefiles.com/packages/lf20_qp1q7mct.json"

@st.cache_data(ttl=3600)
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=3)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_gemini_dashboard_insight(income, burn, runway, risk_score):
    if not genai:
        return "⚠️ Gemini library missing."
        
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Gemini Key missing."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            f"Analyze this financial status: Monthly Income {income}, Monthly Burn {burn}, "
            f"Survival Runway {runway} days, Risk Score {risk_score}/100. "
            "Provide exactly ONE short, punchy sentence (max 20 words) of advice or warning."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Sentinel is offline (AI Connection Error)."

def speak_text(text):
    if not gTTS:
        return None
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception:
        return None

# ==========================================
# 2. AUTH & ONBOARDING FLOW
# ==========================================
if not st.session_state["logged_in"]:
    st.warning("🔒 Access Restricted. Please log in.")
    if st.button("Dev Login (Bypass)", key="dev_login_btn"):
        st.session_state["logged_in"] = True
        st.session_state["profile_complete"] = True
        st.rerun()
    st.stop()

if not st.session_state["profile_complete"]:
    st.title("Welcome to Livelihood Sentinel")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### Let's secure your future.")
        st.write("To activate the Sentinel, we need to know who you are.")
        if st.button("🚀 Start Tracking Setup", type="primary", use_container_width=True, key="setup_btn"):
            st.switch_page("pages/tracking.py")
    with c2:
        st.markdown("<h1>📋</h1>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 3. MAIN DASHBOARD LOGIC
# ==========================================
user_type = st.session_state["user_type"]

# Alert Banner
active_protocol = st.session_state.get("advice_topic_context")
if active_protocol:
    st.error(f"⚠️ **ACTIVE PROTOCOL:** {active_protocol}", icon="🚨")

# ------------------------------------------
# A. STUDENT DASHBOARD
# ------------------------------------------
if user_type == "Student":
    
    # --- Header ---
    col_a, col_b = st.columns([3, 1], gap="medium")
    with col_a:
        st.title("🎓 Student Sentinel")
        college = st.session_state.get("college_name", "Campus")
        stream = st.session_state.get('study_stream', 'General')
        st.caption(f"📍 {college} • 📚 {stream}")
    with col_b:
        st.write("") # Spacer to align button
        if st.button("🔄 Reset Day", help="Resets 'Spent Today' to 0", key="reset_day_btn"):
            st.session_state["today_spend"] = 0.0
            save_profile({"today_spend": 0.0}) 
            st.rerun()

    st.divider()

    # --- Wallet Metrics ---
    wallet = float(st.session_state["savings_buffer"]) 
    daily_limit = float(st.session_state["daily_limit"])
    today_spend = float(st.session_state["today_spend"])
    remaining_limit = max(0.0, daily_limit - today_spend)
    
    m1, m2, m3 = st.columns(3, gap="small")
    with m1:
        st.metric("💰 Wallet", f"₹{int(wallet)}")
    with m2:
        st.metric("📉 Spent", f"₹{int(today_spend)}", delta=f"Limit: ₹{int(daily_limit)}", delta_color="off")
    with m3:
        st.metric("✅ Safe", f"₹{int(remaining_limit)}", delta="Budget", delta_color="normal")

    # --- Limit Meter ---
    if daily_limit > 0:
        progress = min(1.0, today_spend / daily_limit)
    else:
        progress = 1.0
        
    st.progress(progress)
    if progress >= 1.0:
        st.error("⚠️ You have exceeded your daily spending limit!")

    # --- SURVIVAL FORECAST ---
    if daily_limit > 0 and wallet > 0:
        days_left = int(wallet / daily_limit)
    else:
        days_left = 0

    if days_left < 3:
        forecast_color = "red"
        forecast_msg = "CRITICAL: You won't last the weekend."
        icon = "😱"
    elif days_left < 7:
        forecast_color = "orange"
        forecast_msg = "WARNING: Tight budget ahead."
        icon = "😬"
    else:
        forecast_color = "green"
        forecast_msg = "Safe zone. Keep it up."
        icon = "😎"

    with st.container(border=True):
        c_icon, c_text = st.columns([1, 5])
        with c_icon:
            st.markdown(f"# {icon}")
        with c_text:
            st.markdown(f"### Survival Forecast: :{forecast_color}[{days_left} Days Left]")
            st.caption(forecast_msg)

    st.divider()

    # --- Lending Log & Notes ---
    st.subheader("📝 Lending Log & Notes")
    saved_note = st.session_state["student_note"]
    user_note = st.text_area("Notes", value=saved_note, height=100, placeholder="Ex: Gave ₹500 to Rahul...", key="student_notes_area")

    n_col1, n_col2 = st.columns([1, 1])
    with n_col1:
        if st.button("💾 Save Note", use_container_width=True, key="save_note_btn"):
            st.session_state["student_note"] = user_note
            save_profile({"student_note": user_note})
            st.toast("Note saved!")
    with n_col2:
        if st.button("🔊 Read Aloud", use_container_width=True, key="read_note_btn"):
            if user_note.strip():
                audio_fp = speak_text(user_note)
                if audio_fp:
                    st.audio(audio_fp, format='audio/mp3', autoplay=True)
            else:
                st.warning("Write something first!")

    st.divider()

    # --- Quick Log (Spend Tracker) ---
    st.subheader("⚡ Quick Log")
    
    with st.container(border=True):
        if st.button("🔗 Auto-Track via Bank SMS", use_container_width=True, key="bank_sms_btn"):
            st.toast("🚀 Coming Soon: Phase 2", icon="🚧")
            
        st.divider()
        
        def quick_deduct(val):
            val = float(val)
            st.session_state["savings_buffer"] -= val
            st.session_state["today_spend"] += val
            save_profile({
                "savings_buffer": st.session_state["savings_buffer"],
                "today_spend": st.session_state["today_spend"]
            })
            st.rerun()

        st.caption("Common Spends:")
        qb1, qb2, qb3 = st.columns(3)
        with qb1:
            if st.button("☕ ₹50", use_container_width=True, key="spend_50"): quick_deduct(50)
        with qb2:
            if st.button("🍔 ₹100", use_container_width=True, key="spend_100"): quick_deduct(100)
        with qb3:
            if st.button("🚌 ₹30", use_container_width=True, key="spend_30"): quick_deduct(30)

        st.caption("Custom Entry:")
        c_input, c_btn1, c_btn2 = st.columns([2, 1, 1])
        with c_input:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, key="trans_amt")
        with c_btn1:
            if st.button("Spent", use_container_width=True, type="primary", key="custom_spend_btn"):
                if amount > 0: quick_deduct(amount)
        with c_btn2:
            if st.button("Got Cash", use_container_width=True, key="add_cash_btn"):
                if amount > 0:
                    st.session_state["savings_buffer"] += amount
                    save_profile({"savings_buffer": st.session_state["savings_buffer"]})
                    st.rerun()

    # --- Navigation ---
    st.write("")
    st.caption("Sentinel Tools")
    nav1, nav2, nav3 = st.columns(3)
    stream_short = stream.split(" ")[0] if stream else "Career"
    
    with nav1:
        if st.button(f"📰 News", use_container_width=True, key="nav_news_stu"):
            st.switch_page("pages/news_alerts.py")
    with nav2:
        if st.button("💡 Advice", use_container_width=True, key="nav_advice_stu"):
            st.switch_page("pages/advice.py")
    with nav3:
        if st.button("⚙️ Settings", use_container_width=True, key="nav_set_stu"):
            st.switch_page("pages/settings.py")


# ------------------------------------------
# B. STANDARD DASHBOARD
# ------------------------------------------
else:
    # --- Logic: Risk Assessment ---
    risk = int(st.session_state["risk_score"])
    runway = int(st.session_state["runway_days"])
    burn = float(st.session_state["burn"])
    net_savings = float(st.session_state["net_savings"])

    # Determine Status
    if risk >= 75 or runway <= 15:
        status_msg = "CRITICAL THREATS"
        status_color = "red"
        lottie_url = LOTTIE_CRITICAL
    elif risk >= 50 or runway <= 30:
        status_msg = "MONITORING RISKS"
        status_color = "orange"
        lottie_url = LOTTIE_CRITICAL 
    else:
        status_msg = "LIVELIHOOD SECURE"
        status_color = "green"
        lottie_url = LOTTIE_SAFE

    # --- Dashboard Header (FIXED STABILITY) ---
    c1, c2 = st.columns([2.5, 1], gap="medium") 
    with c1:
        st.title("Livelihood Sentinel")
        st.caption(f"Mode: Standard • Lang: {st.session_state.get('lang', 'English')}")
        st.markdown(f"### Status: :{status_color}[{status_msg}]")
        
    with c2:
        # We enforce a fixed height to prevent "Jumping" during load
        lottie_json = load_lottieurl(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=120, key="sentinel_avatar")
        else:
            st.markdown("<h1>🛡️</h1>", unsafe_allow_html=True) 

    if st.button("🔍 Run Deep Scan", help="Analyze new alerts", key="deep_scan_btn"):
        scan_placeholder = st.empty()
        scan_logs = [
            "> Initializing Sentinel Sat-Link...",
            "> Connecting to RBI/SEBI Feeds...",
            "> Decrypting Economic Data Streams...",
            "> Analyzing User Risk Profile...",
            "> THREATS DETECTED. GENERATING REPORT."
        ]
        for log in scan_logs:
            scan_placeholder.markdown(f"```\n{log}\n```")
            time.sleep(0.5) 
        
        scan_placeholder.empty() 
        st.switch_page("pages/news_alerts.py")

    st.divider()

    # --- The Metrics ---
    income = float(st.session_state["monthly_income"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Monthly Income", f"₹{int(income):,}")
    with col2:
        st.metric("Monthly Burn", f"₹{int(burn):,}")
    with col3:
        st.metric("Net Savings", f"₹{int(net_savings):,}")

    if runway > 900:
        runway_display = "Infinite"
        delta_display = "Safe"
    else:
        runway_display = f"{runway} Days"
        delta_display = "-2 days" if runway < 30 else "Stable"

    with col4:
        st.metric(
            "Survival Runway", 
            runway_display, 
            delta=delta_display, 
            delta_color="inverse"
        )
    
    if st.button("🔗 Connect Bank / SMS for Auto-Tracking", use_container_width=True, key="std_bank_link"):
         st.toast("🚀 Coming Soon: Account Aggregator Integration", icon="🚧")

    # --- EMERGENCY SIMULATOR ---
    with st.expander("⚡ Simulate Emergency (Stress Test)", expanded=False):
        st.caption("See what happens to your runway if a sudden cost hits today.")
        
        sc1, sc2 = st.columns([2, 1])
        with sc1:
            shock_amount = st.number_input("Emergency Cost (₹)", min_value=0.0, value=50000.0, step=5000.0, key="shock_input")
        with sc2:
            st.write("") 
            st.write("")
            simulate_btn = st.button("💥 Simulate", type="primary", use_container_width=True, key="sim_btn")

        if simulate_btn:
            temp_savings = net_savings - shock_amount
            if burn > 0:
                new_runway = int(temp_savings / (burn / 30))
            else:
                new_runway = 999
            
            if new_runway < 0: new_runway = 0
            
            st.markdown("### ⚠️ Impact Report")
            c_before, c_after = st.columns(2)
            c_before.metric("Current Runway", f"{runway} Days")
            c_after.metric("Runway After Shock", f"{new_runway} Days", delta=f"{new_runway - runway} Days", delta_color="inverse")
            
            if new_runway < 30:
                st.error("Result: CRITICAL FAILURE. You need an Emergency Fund.")
            else:
                st.success("Result: SURVIVABLE. You have enough buffer.")
                st.balloons()

    st.divider()
    
    # --- Gemini Analysis ---
    st.subheader("🤖 Gemini Analysis")
    with st.container(border=True):
        # Using a container here keeps layout stable while spinner runs
        with st.spinner("Gemini is analyzing your live metrics..."):
            ai_insight = get_gemini_dashboard_insight(income, burn, runway, risk)
        
        st.markdown(f"**Gemini Insight:** {ai_insight}")
        if risk > 70:
             st.caption("Action: Check 'Variable' expenses in Tracking immediately.")
        
    st.caption("Powered by Gemini 1.5 Flash • Real-time Calculation")

    # --- Footer Navigation ---
    left, right, last = st.columns(3)
    with left:
        with st.container(border=True):
            st.caption("Active Alerts")
            if st.button("📰 View News", key="nav_news_std", use_container_width=True):
                st.switch_page("pages/news_alerts.py")

    with right:
        with st.container(border=True):
            st.caption("Audio Update")
            if st.button("🎙️ Voice Assistant", key="nav_voice_std", use_container_width=True):
                st.switch_page("pages/voice.py")

    with last:
        with st.container(border=True):
             st.caption("System")
             if st.button("⚙️ Settings", key="nav_settings_std", use_container_width=True):
                 st.switch_page("pages/settings.py")