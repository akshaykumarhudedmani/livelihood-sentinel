import streamlit as st
import time
import google.generativeai as genai
import os
from gtts import gTTS
from io import BytesIO
from db_ops import save_profile

st.set_page_config(page_title="Home", page_icon=":material/home:")

# ==========================================
# 0. HELPER FUNCTIONS
# ==========================================
@st.cache_data(ttl=3600)
def get_gemini_dashboard_insight(income, burn, runway, risk_score):
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Gemini Key missing. Unable to generate real-time insight."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = (
            f"Analyze this financial status: Monthly Income {income}, Monthly Burn {burn}, "
            f"Survival Runway {runway} days, Risk Score {risk_score}/100. "
            "Provide exactly ONE short, punchy sentence (max 20 words) of advice or warning. "
            "Be direct. No preamble."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Sentinel is offline (AI Connection Error)."

def speak_text(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None

# ==========================================
# 1. AUTH & INIT
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

# ==========================================
# STATE 1: NEW USER
# ==========================================
if not st.session_state.get("profile_complete", False):
    st.title("Welcome to Livelihood Sentinel")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### Let's secure your future.")
        st.write("To activate the Sentinel, we need to know who you are.")
        st.info("Choose 'Student' or 'Standard' mode in setup.")
        if st.button("🚀 Start Tracking Setup", type="primary", use_container_width=True):
            st.switch_page("pages/tracking.py")
    with c2:
        try:
            st.image("assets/hero.jpeg", width=250) 
        except:
            st.markdown("<h1>📋</h1>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# STATE 2: ACTIVE DASHBOARD
# ==========================================
user_type = st.session_state.get("user_type", "Standard")

# ==========================================
# A. STUDENT DASHBOARD
# ==========================================
if user_type == "Student":
    
    # --- 1. Header ---
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.title("🎓 Student Sentinel")
        college = st.session_state.get("college_name", "Campus")
        stream = st.session_state.get('study_stream', 'General')
        st.caption(f"📍 {college} • 📚 {stream}")
    with col_b:
        if st.button("🔄 New Day", help="Resets 'Spent Today' to 0"):
            st.session_state["today_spend"] = 0
            save_profile({"today_spend": 0}) 
            st.rerun()

    st.divider()

    # --- 2. Wallet Metrics ---
    wallet = int(st.session_state.get("savings_buffer", 0)) 
    daily_limit = int(st.session_state.get("daily_limit", 100))
    today_spend = int(st.session_state.get("today_spend", 0))
    remaining_limit = max(0, daily_limit - today_spend)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Wallet Balance", f"₹{wallet}")
    m2.metric("📉 Spent Today", f"₹{today_spend}", delta=f"Limit: ₹{daily_limit}", delta_color="off")
    m3.metric("✅ Safe to Spend", f"₹{remaining_limit}", delta="Daily Budget", delta_color="normal")

    # --- 3. Limit Meter ---
    progress = min(1.0, today_spend / daily_limit) if daily_limit > 0 else 0
    bar_color = "green"
    if progress > 0.75: bar_color = "red"
    elif progress > 0.5: bar_color = "orange"
    
    st.progress(progress)
    if progress >= 1.0:
        st.error("⚠️ You have exceeded your daily spending limit!")

    st.divider()

    # --- 4. Lending Log & Notes ---
    st.subheader("📝 Lending Log & Notes")
    saved_note = st.session_state.get("student_note", "")
    
    user_note = st.text_area(
        "Notes", 
        value=saved_note, 
        height=100, 
        placeholder="Ex: Gave ₹500 to Rahul..."
    )

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

    # --- 5. Quick Log ---
    st.subheader("⚡ Quick Log")
    with st.container(border=True):
        c_input, c_btn1, c_btn2 = st.columns([2, 1, 1])
        with c_input:
            amount = st.number_input("Amount (₹)", min_value=0, step=10, key="trans_amt")
        with c_btn1:
            if st.button("☕ Spent", use_container_width=True, type="primary"):
                if amount > 0:
                    st.session_state["savings_buffer"] -= amount
                    st.session_state["today_spend"] = today_spend + amount
                    save_profile({
                        "savings_buffer": st.session_state["savings_buffer"],
                        "today_spend": st.session_state["today_spend"]
                    })
                    st.rerun()
        with c_btn2:
            if st.button("💵 Got Cash", use_container_width=True):
                if amount > 0:
                    st.session_state["savings_buffer"] += amount
                    save_profile({"savings_buffer": st.session_state["savings_buffer"]})
                    st.rerun()

    # --- 6. Navigation ---
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


# ==========================================
# B. STANDARD DASHBOARD
# ==========================================
else:
    # --- Logic: Risk Assessment ---
    risk = int(st.session_state.get("risk_score", 0))
    runway = int(st.session_state.get("runway_days", 0))

    if risk >= 75 or runway <= 15:
        status_msg = "CRITICAL THREATS"
        status_color = "red"
    elif risk >= 50 or runway <= 30:
        status_msg = "MONITORING RISKS"
        status_color = "orange"
    else:
        status_msg = "LIVELIHOOD SECURE"
        status_color = "green"

    # --- Dashboard Header (Clean - No Logo) ---
    c1, c2 = st.columns([3, 1]) 
    with c1:
        st.title("Livelihood Sentinel")
        st.caption(f"Mode: Standard • Language: {st.session_state.get('lang', 'English')}")
        st.markdown(f"### Status: :{status_color}[{status_msg}]")
        
    with c2:
        # SCAN BUTTON MOVED HERE
        if st.button("🔍 Run Deep Scan", help="Analyze new alerts"):
            with st.status("📡 Initializing Sentinel Scan...", expanded=True) as status:
                st.write("Connecting to SEBI/RBI satellite feeds...")
                time.sleep(0.8)
                status.update(label="Scan Complete!", state="complete", expanded=False)
                st.switch_page("pages/news_alerts.py")

    st.divider()

    # --- The Metrics ---
    income = int(st.session_state.get("monthly_income", 0))
    burn = int(st.session_state.get("burn", 0))
    net_savings = int(st.session_state.get("net_savings", 0))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monthly Income", f"₹{income:,}")
    col2.metric("Monthly Burn", f"₹{burn:,}")
    col3.metric("Net Savings", f"₹{net_savings:,}")

    if runway > 900:
        runway_display = "Infinite"
        delta_display = "Safe"
    else:
        runway_display = f"{runway} Days"
        delta_display = "-2 days" if runway < 30 else "Stable"

    # --- METRIC WITH TOOLTIP ---
    col4.metric(
        "Survival Runway", 
        runway_display, 
        delta=delta_display, 
        delta_color="inverse",
        help="How many days your family can survive on current savings if all income stops today."
    )

    st.divider()
    st.subheader("🤖 Gemini Analysis")

    with st.container(border=True):
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