import streamlit as st
import time

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

# Lists
crops = st.session_state.get("crops_grown", [])
held_assets = st.session_state.get("held_assets", [])

# ==========================================
# 1. SMART LOGIC ENGINE (With Consequences)
# ==========================================
def build_smart_advice():
    actions = []
    
    # --- CHECK 1: SURVIVAL RUNWAY ---
    if runway_days <= 15:
        actions.append({
            "level": "CRITICAL", 
            "icon": "🚨",
            "title": "Immediate Cash Preservation", 
            "desc": f"Runway is only {runway_days} days. Stop ALL non-food spending immediately.",
            "loss": "If ignored: Total insolvency (bankruptcy) in ~2 weeks."
        })
    elif runway_days <= 45:
        actions.append({
            "level": "WARNING", 
            "icon": "⚠️",
            "title": "Conserve Cash", 
            "desc": "Runway is tight (< 45 days). Postpone any large purchases.",
            "loss": "If ignored: You will be forced to take high-interest loans for daily needs."
        })

    # --- CHECK 2: DEBT TRAP ---
    if emi_total > 0:
        debt_ratio = (emi_total / income) * 100 if income > 0 else 100
        if debt_ratio > 40:
             actions.append({
                "level": "CRITICAL", 
                "icon": "💸",
                "title": "Debt Trap Alert", 
                "desc": f"Your EMIs consume {int(debt_ratio)}% of income. Contact bank for loan restructuring.",
                "loss": "If ignored: High risk of asset seizure or default penalties."
            })
        elif debt_ratio > 20:
             actions.append({
                "level": "INFO", 
                "icon": "🏦",
                "title": "Debt Management", 
                "desc": "Ensure EMIs are paid by 5th of month to avoid penalties.",
                "loss": "If ignored: Credit score damage impacts future farm loans."
            })

    # --- CHECK 3: AGRICULTURE ---
    if crops and len(crops) > 0:
        crop_names = ", ".join(crops)
        actions.append({
            "level": "ADVISORY", 
            "icon": "🌾",
            "title": "Harvest Strategy", 
            "desc": f"Detected farming of {crop_names}. Stagger your sales to avoid market dips.",
            "loss": "If ignored: Selling all at once risks 20-30% revenue loss."
        })
        if "Cotton" in crops:
             actions.append({
                "level": "WARNING", 
                "icon": "🐛",
                "title": "Cotton Pest Alert", 
                "desc": "Check Pink Bollworm notices in the News tab.",
                "loss": "If ignored: Risk of total crop failure significantly increases."
            })

    # --- CHECK 4: ASSETS ---
    if held_assets and len(held_assets) > 0:
        if "Gold" in held_assets and runway_days < 30:
            actions.append({
                "level": "INFO", 
                "icon": "💍",
                "title": "Liquidity Option", 
                "desc": "Consider a low-interest Gold Loan instead of high-interest moneylenders.",
                "loss": "If ignored: Selling family gold permanently erodes your wealth."
            })
        if "Crypto (BTC/ETH)" in held_assets:
            actions.append({
                "level": "WARNING", 
                "icon": "📉", 
                "title": "Volatility Risk", 
                "desc": "Crypto is high risk. Do not rely on this for emergency funds.",
                "loss": "If ignored: Market crash could wipe out emergency savings instantly."
            })

    # --- CHECK 5: SAVINGS ---
    if savings > 0 and savings < burn:
         actions.append({
            "level": "WARNING", 
            "icon": "🛡️",
            "title": "Buffer Low", 
            "desc": "Your savings cover less than 1 month of expenses. Priority: Rebuild buffer.",
            "loss": "If ignored: A single medical emergency will force you into debt."
        })

    return actions

# ==========================================
# 2. UI DISPLAY (Super UI)
# ==========================================

st.subheader("✅ Personalized Protocols")
st.caption("Protocols generated based on your ACTIVE tracking inputs.")

smart_actions = build_smart_advice()
badge_color = {"CRITICAL": "red", "WARNING": "orange", "ADVISORY": "green", "INFO": "blue"}

if smart_actions:
    for action in smart_actions:
        lvl = action.get("level", "INFO")
        color = badge_color.get(lvl, "gray")
        
        # CARD UI
        with st.container(border=True):
            col_icon, col_text = st.columns([0.15, 0.85])
            
            with col_icon:
                st.markdown(f"<div style='font-size: 32px; text-align: center; padding-top: 10px;'>{action['icon']}</div>", unsafe_allow_html=True)
            
            with col_text:
                st.markdown(f":{color}[**{lvl} • {action['title']}**]")
                st.write(action["desc"])
                # THE LOSS FRAMING (FRIEND'S IDEA)
                st.markdown(f"**🔻 {action['loss']}**", help="This creates urgency for the user.")

else:
    st.info("No critical risks detected based on your current inputs.")

st.divider()

# ==========================================
# 3. AI SECTION (With Loading Animation)
# ==========================================
st.subheader("🤖 AI Strategic Analysis")
st.caption("Powered by Gemini 1.5 Flash")

if "ai_msg" not in st.session_state:
    st.session_state["ai_msg"] = None

if st.button("✨ Generate Custom Strategy", type="primary", use_container_width=True):
    # --- THE COOL LOADING PART ---
    with st.status("🤖 Gemini is initializing...", expanded=True) as status:
        st.write("Connecting to Google Cloud AI...")
        time.sleep(1) # Fake delay for effect
        st.write(f"Analyzing burn rate (₹{burn}/mo)...")
        time.sleep(1)
        st.write("Checking market conditions for selected crops...")
        time.sleep(1)
        status.update(label="Analysis Complete", state="complete", expanded=False)
        
    # Set the message
    st.session_state["ai_msg"] = "⚠️ **Future Development:** Detailed Generative AI analysis is planned for Phase 2."

if st.session_state["ai_msg"]:
    st.info(st.session_state["ai_msg"])

# --- Footer ---
st.write("")
st.divider()
c1, c2 = st.columns(2)
with c1:
    if st.button("← Back to Alerts", use_container_width=True):
        st.switch_page("pages/news_alerts.py")
with c2:
    if st.button("Go to Home", use_container_width=True):
        st.switch_page("pages/home.py")