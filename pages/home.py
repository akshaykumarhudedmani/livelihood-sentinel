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
    # Fallback if db_ops.py is missing or renamed
    def save_profile(data):
        pass

# ==========================================
# 0. PAGE CONFIG & INIT
# ==========================================
st.set_page_config(
    page_title="Livelihood Sentinel", 
    page_icon=":material/shield:",
    layout="wide"  # <--- CHANGED TO "wide" AS REQUESTED
)

# --- CSS Stabilizer (Kept from previous fix to prevent jumping) ---
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { overflow-y: scroll; }
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    </style>
""", unsafe_allow_html=True)

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
        "advice_topic_context": None,
        # NEW STATE VARIABLES FOR CONFIRMATION
        "pending_deduct": None,
        "show_success_msg": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_state()

# ==========================================
# 1. HELPER FUNCTIONS & ASSETS
# ==========================================

# Asset URLs
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
        return "⚠️ Gemini Key missing. Unable to generate real-time insight."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = (
            f"Analyze this financial status: Monthly Income {income}, Monthly Burn {burn}, "
            f"Survival Runway {runway} days, Risk Score {risk_score}/100. "
            "Provide exactly ONE short, punchy sentence (max 20 words) of advice or warning. "
            "Be direct. No preamble."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "sorry for inconvenience! ,gemini 2.5 flash's credit has been currently overused, please check again later."

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
    
    if st.button("Dev Login (Bypass)"):
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
        st.info("Choose 'Student' or 'Standard' mode in setup.")
        if st.button("🚀 Start Tracking Setup", type="primary", use_container_width=True):
            st.switch_page("pages/tracking.py")
    with c2:
        st.markdown("<h1>📋</h1>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 3. MAIN DASHBOARD LOGIC
# ==========================================
user_type = st.session_state["user_type"]

active_protocol = st.session_state.get("advice_topic_context")
if active_protocol:
    st.error(f"⚠️ **ACTIVE DEFENSE PROTOCOL:** {active_protocol} (Check Advice Page)", icon="🚨")

# ------------------------------------------
# A. STUDENT DASHBOARD
# ------------------------------------------
if user_type == "Student":
    
    # --- Header ---
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.title("🎓 Student Sentinel")
        college = st.session_state.get("college_name", "Campus")
        stream = st.session_state.get('study_stream', 'General')
        st.caption(f"📍 {college} • 📚 {stream}")
    with col_b:
        st.write("") # Spacer
        if st.button("🔄 Reset Day", help="Resets 'Spent Today' to 0", use_container_width=True):
            st.session_state["today_spend"] = 0.0
            save_profile({"today_spend": 0.0}) 
            st.rerun()

    st.divider()

    # --- Wallet Metrics ---
    wallet = float(st.session_state["savings_buffer"]) 
    daily_limit = float(st.session_state["daily_limit"])
    today_spend = float(st.session_state["today_spend"])
    remaining_limit = max(0.0, daily_limit - today_spend)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Wallet Balance", f"₹{int(wallet)}")
    m2.metric("📉 Spent Today", f"₹{int(today_spend)}", delta=f"Limit: ₹{int(daily_limit)}", delta_color="off")
    m3.metric("✅ Safe to Spend", f"₹{int(remaining_limit)}", delta="Daily Budget", delta_color="normal")

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
    user_note = st.text_area("Notes", value=saved_note, height=100, placeholder="Ex: Gave ₹500 to Rahul...")

    n_col1, n_col2 = st.columns([1, 1])
    with n_col1:
        if st.button("💾 Save Note", use_container_width=True):
            st.session_state["student_note"] = user_note
            save_profile({"student_note": user_note})
            st.toast("Note saved!")
    with n_col2:
        if st.button("🔊 Read Aloud", use_container_width=True):
            if user_note.strip():
                audio_fp = speak_text(user_note)
                if audio_fp:
                    st.audio(audio_fp, format='audio/mp3', autoplay=True)
            else:
                st.warning("Write something first!")

    st.divider()

    # --- Quick Log ---
    st.subheader("⚡ Quick Log", help="Add your daily expenses here manually.")
    
    with st.container(border=True):
        if st.button("🔗 Auto-Track via Bank SMS", help="Link your bank SMS", use_container_width=True):
            st.toast("🚀 Coming Soon: Account Aggregator Integration", icon="🚧")
            
        st.divider()
        
        # --- SUCCESS MESSAGE DISPLAY ---
        if st.session_state.get("show_success_msg"):
             st.success("✅ Log Added Successfully! Dashboard Updated.", icon="💸")
             # Reset the flag so it doesn't show forever (requires another rerun eventually or user action)
             # For now, it stays until next action, which is fine for visibility.

        # --- CONFIRMATION DIALOG LOGIC ---
        pending_amt = st.session_state.get("pending_deduct")

        if pending_amt is not None:
            # Show Confirmation Box
            st.warning(f"⚠️ **Wait!** Are you sure you want to log **₹{pending_amt}**?")
            col_yes, col_no = st.columns(2)
            
            with col_yes:
                if st.button("✅ YES, CONFIRM", use_container_width=True, type="primary"):
                    # Perform Deduction
                    val = float(pending_amt)
                    st.session_state["savings_buffer"] -= val
                    st.session_state["today_spend"] += val
                    save_profile({
                        "savings_buffer": st.session_state["savings_buffer"],
                        "today_spend": st.session_state["today_spend"]
                    })
                    # Clear pending and show success
                    st.session_state["pending_deduct"] = None
                    st.session_state["show_success_msg"] = True
                    st.toast("Spending Recorded!", icon="📉")
                    st.rerun()
            
            with col_no:
                if st.button("❌ CANCEL", use_container_width=True):
                    st.session_state["pending_deduct"] = None
                    st.session_state["show_success_msg"] = False
                    st.rerun()

        else:
            # Show Standard Buttons (Only visible if not confirming)
            st.caption("Common Spends:")
            qb1, qb2, qb3 = st.columns(3)
            
            # These buttons now just set the 'pending_deduct' state
            with qb1:
                if st.button("☕ ₹50", use_container_width=True): 
                    st.session_state["pending_deduct"] = 50.0
                    st.rerun()
            with qb2:
                if st.button("🍔 ₹100", use_container_width=True): 
                    st.session_state["pending_deduct"] = 100.0
                    st.rerun()
            with qb3:
                if st.button("🚌 ₹30", use_container_width=True): 
                    st.session_state["pending_deduct"] = 30.0
                    st.rerun()

            st.caption("Custom Entry:")
            c_input, c_btn1, c_btn2 = st.columns([2, 1, 1])
            with c_input:
                amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, key="trans_amt")
            with c_btn1:
                if st.button("Spent", use_container_width=True):
                    if amount > 0: 
                        st.session_state["pending_deduct"] = amount
                        st.rerun()
            with c_btn2:
                # "Got Cash" is positive, handle immediately or confirm? 
                # Keeping it immediate for now as it adds money, less risky.
                if st.button("Got Cash", use_container_width=True):
                    if amount > 0:
                        st.session_state["savings_buffer"] += amount
                        save_profile({"savings_buffer": st.session_state["savings_buffer"]})
                        st.toast("Cash Added!", icon="💰")
                        st.rerun()

    # --- Navigation ---
    st.write("")
    st.caption("Sentinel Tools")
    nav1, nav2, nav3 = st.columns(3)
    stream_short = stream.split(" ")[0] if stream else "Career"
    
    with nav1:
        if st.button(f"📰 {stream_short} News", use_container_width=True):
            st.switch_page("pages/news_alerts.py")
    with nav2:
        if st.button("💡 Money Advice", use_container_width=True):
            st.switch_page("pages/advice.py")
    with nav3:
        if st.button("⚙️ Settings", use_container_width=True):
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

    # Determine Status & Animation
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

    # --- Dashboard Header ---
    c1, c2 = st.columns([3, 1]) 
    with c1:
        st.title("Livelihood Sentinel")
        st.caption(f"Mode: Standard • Language: {st.session_state.get('lang', 'English')}")
        st.markdown(f"### Status: :{status_color}[{status_msg}]")
        
    with c2:
        lottie_json = load_lottieurl(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=150, key="sentinel_avatar")
        else:
            st.markdown("<h1>🛡️</h1>", unsafe_allow_html=True) 

    if st.button("🔍 Run Deep Scan", help="Analyze new alerts"):
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
    col1.metric("Monthly Income", f"₹{int(income):,}")
    col2.metric("Monthly Burn", f"₹{int(burn):,}")
    col3.metric("Net Savings", f"₹{int(net_savings):,}")

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
        delta_color="inverse",
        help="How many days your family can survive if income stops."
    )
    
    # -- Bank Link --
    if st.button("🔗 Connect Bank / SMS for Auto-Tracking", use_container_width=True):
         st.toast("🚀 Coming Soon: Account Aggregator Integration", icon="🚧")

    # --- EMERGENCY SIMULATOR ---
    with st.expander("⚡ Simulate Emergency (Stress Test)", expanded=False):
        st.caption("See what happens to your runway if a sudden cost hits today.")
        
        sc1, sc2 = st.columns([2, 1])
        with sc1:
            shock_amount = st.number_input("Emergency Cost (₹)", min_value=0.0, value=50000.0, step=5000.0)
        with sc2:
            st.write("") 
            st.write("")
            simulate_btn = st.button("💥 Simulate", type="primary", use_container_width=True)

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
        with st.spinner("Gemini is analyzing your live metrics..."):
            ai_insight = get_gemini_dashboard_insight(income, burn, runway, risk)
        
        st.markdown(f"**Gemini Insight:** {ai_insight}")
        if risk > 70:
             st.caption("Action: Check 'Variable' expenses in Tracking immediately.")
        
    st.caption("Powered by Gemini 2.5 Flash • Real-time Calculation")

    # --- Footer Navigation ---
    left, right, last = st.columns(3)
    with left:
        with st.container(border=True):
            st.caption("Active Alerts")
            if st.button("📰 View News", key="nav_news", use_container_width=True):
                st.switch_page("pages/news_alerts.py")

    with right:
        with st.container(border=True):
            st.caption("Audio Update")
            if st.button("🎙️ Voice Assistant", key="nav_voice", use_container_width=True):
                st.switch_page("pages/voice.py")

    with last:
        with st.container(border=True):
             st.caption("System")
             if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
                 st.switch_page("pages/settings.py")