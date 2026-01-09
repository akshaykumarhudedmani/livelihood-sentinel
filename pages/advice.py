import streamlit as st
import time
import google.generativeai as genai
from google.api_core import exceptions
import os

st.set_page_config(page_title="Advice", page_icon=":material/lightbulb:")

# ==========================================
# 0. AUTH & DATA GATES
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

st.title("💡 Strategic Advice")
st.caption("Tactical protocols tailored to your specific assets.")
st.divider()

if not st.session_state.get("profile_complete", False):
    with st.container(border=True):
        st.subheader("Setup required")
        st.write("Complete **Tracking** first to view advice protocols.")
        if st.button("Go to Tracking"):
            st.switch_page("pages/tracking.py")
    st.stop()

# --- Read Specific Data to Filter Advice ---
income = int(st.session_state.get("monthly_income", 0))
emi_total = int(st.session_state.get("emi_total", 0))
burn = int(st.session_state.get("burn", 0))
runway_days = int(st.session_state.get("runway_days", 0))
savings = int(st.session_state.get("savings_buffer", 0))
crops = st.session_state.get("crops_grown", [])
held_assets = st.session_state.get("held_assets", [])

# ==========================================
# 1. SMART LOGIC ENGINE (Rules Based)
# ==========================================
def build_smart_advice():
    actions = []
    
    # --- CHECK 1: SURVIVAL RUNWAY ---
    if runway_days <= 15:
        actions.append({
            "level": "CRITICAL", "icon": "🚨",
            "title": "Immediate Cash Preservation", 
            "desc": f"Runway is only {runway_days} days. Stop ALL non-food spending immediately.",
            "loss": "If ignored: Total insolvency (bankruptcy) in ~2 weeks."
        })
    elif runway_days <= 45:
        actions.append({
            "level": "WARNING", "icon": "⚠️",
            "title": "Conserve Cash", 
            "desc": "Runway is tight (< 45 days). Postpone any large purchases.",
            "loss": "If ignored: You will be forced to take high-interest loans for daily needs."
        })

    # --- CHECK 2: DEBT TRAP ---
    if emi_total > 0:
        debt_ratio = (emi_total / income) * 100 if income > 0 else 100
        if debt_ratio > 40:
             actions.append({
                "level": "CRITICAL", "icon": "💸",
                "title": "Debt Trap Alert", 
                "desc": f"Your EMIs consume {int(debt_ratio)}% of income. Contact bank for loan restructuring.",
                "loss": "If ignored: High risk of asset seizure or default penalties."
            })

    # --- CHECK 3: AGRICULTURE ---
    if crops:
        crop_names = ", ".join(crops)
        actions.append({
            "level": "ADVISORY", "icon": "🌾",
            "title": "Harvest Strategy", 
            "desc": f"Detected farming of {crop_names}. Stagger your sales to avoid market dips.",
            "loss": "If ignored: Selling all at once risks 20-30% revenue loss."
        })

    return actions

# ==========================================
# 2. UI DISPLAY
# ==========================================
st.subheader("✅ Personalized Protocols")
st.caption("Protocols generated based on your ACTIVE tracking inputs.")

smart_actions = build_smart_advice()
badge_color = {"CRITICAL": "red", "WARNING": "orange", "ADVISORY": "green", "INFO": "blue"}

if smart_actions:
    for action in smart_actions:
        lvl = action.get("level", "INFO")
        color = badge_color.get(lvl, "gray")
        with st.container(border=True):
            col_icon, col_text = st.columns([0.15, 0.85])
            with col_icon:
                st.markdown(f"<div style='font-size: 32px; text-align: center; padding-top: 10px;'>{action['icon']}</div>", unsafe_allow_html=True)
            with col_text:
                st.markdown(f":{color}[**{lvl} • {action['title']}**]")
                st.write(action["desc"])
                st.markdown(f"**🔻 {action['loss']}**")
else:
    st.info("No critical risks detected based on your current inputs.")

st.divider()

# ==========================================
# 3. REAL GEMINI STRATEGIC ANALYSIS (WORKING ALIAS)
# ==========================================
st.subheader("🤖 Gemini Strategic Analysis")
st.caption("Powered by Gemini • Real-time Financial Review")

# Function to call Gemini (SDK Logic with Retry)
def get_gemini_strategy(income, burn, runway, crops, assets, risks):
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "⚠️ Error: GEMINI_API_KEY not found in Secrets."

    # Configure the SDK
    genai.configure(api_key=api_key)
    
    # --- CRITICAL FIX: USING 'gemini-flash-latest' WHICH EXISTS IN YOUR LIST ---
    model = genai.GenerativeModel('gemini-flash-latest')

    # Construct the User Persona for AI
    profile_desc = (
        f"User is a gig-worker/farmer in India.\n"
        f"Monthly Income: ₹{income}\n"
        f"Monthly Burn: ₹{burn}\n"
        f"Survival Runway: {runway} days\n"
        f"Crops Grown: {', '.join(crops) if crops else 'None'}\n"
        f"Assets: {', '.join(assets) if assets else 'None'}\n"
        f"Identified Risks: {risks}\n"
    )

    prompt_text = (
        f"Act as 'Livelihood Sentinel', a strict financial guardian.\n"
        f"Analyze this user profile:\n{profile_desc}\n"
        f"Task: Give 3 specific, actionable bullet points to extend their survival runway. "
        f"If runway is low, be urgent. If runway is high, suggest growth.\n"
        f"Tone: Direct, protecting, no fluff. Keep it short."
    )

    # Retry Logic (Tries 3 times if error occurs)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt_text)
            return response.text
        except exceptions.ResourceExhausted:
            # Hit rate limit (429)
            if attempt < max_retries - 1:
                time.sleep(5) 
                continue
            else:
                return "⚠️ Server Busy: Rate limit exceeded. Please try again in 30 seconds."
        except Exception as e:
            return f"Gemini Error: {str(e)}"

# UI Container for AI
with st.container(border=True):
    if "ai_strategy_result" not in st.session_state:
        st.session_state["ai_strategy_result"] = None

    # The Trigger Button
    if st.button("✨ Generate Custom Strategy", type="primary", use_container_width=True):
        
        current_risks = [a['title'] for a in smart_actions] 
        
        with st.status("🧠 Gemini is analyzing...", expanded=True) as status:
            st.write("Reading financial profile...")
            time.sleep(0.5)
            
            # THE REAL CALL
            strategy = get_gemini_strategy(
                income=income,
                burn=burn,
                runway=runway_days,
                crops=crops,
                assets=held_assets,
                risks=current_risks
            )
            
            st.session_state["ai_strategy_result"] = strategy
            status.update(label="Strategy Generated!", state="complete", expanded=False)

    # Display Result
    if st.session_state["ai_strategy_result"]:
        st.markdown("### 🛡️ Sentinel Protocol")
        st.markdown(st.session_state["ai_strategy_result"])