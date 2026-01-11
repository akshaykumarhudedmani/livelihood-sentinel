import streamlit as st
import time
import google.generativeai as genai
import os

st.set_page_config(page_title="Advice", page_icon=":material/lightbulb:")

# ==========================================
# 0. AUTH CHECK
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

# ==========================================
# 1. AI ENGINE (Dual Persona)
# ==========================================
def get_gemini_advice(prompt_context, persona_type):
    """
    Fetches AI advice with specific personas and strict error handling.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ System Error: Gemini API Key not found in secrets."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Dual Persona Logic
        if persona_type == "Student":
            system_instruction = (
                "You are a wise, practical college senior/mentor. "
                "Tone: Empathetic, tactical, low-cost, non-judgmental. "
                "Do NOT lecture about long-term investing or stocks. "
                "Focus on: Cheap food hacks, surviving on little money, side hustles, and academic survival. "
                "Keep answers short (max 120 words) and use bullet points."
            )
        else:
            system_instruction = (
                "You are a professional Financial Strategist. "
                "Tone: Serious, objective, risk-focused. "
                "Focus on: Cash preservation, debt reduction (avalanche/snowball), and asset allocation. "
                "Keep answers actionable (max 120 words) and use bullet points."
            )

        full_prompt = f"{system_instruction}\n\nUSER CONTEXT: {prompt_context}"
        
        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
            return "⚠️ **Traffic Overload:** The AI model is currently busy (Rate Limit Reached). Please wait 30 seconds and try again."
        else:
            return f"⚠️ **Connection Error:** Unable to reach Sentinel AI. ({error_msg})"

# ==========================================
# 2. UI SETUP & CONTEXT LOADING
# ==========================================
user_type = st.session_state.get("user_type", "Standard")

# Check for "Protocol Link" from News Page
protocol_context = st.session_state.get("advice_topic_context", None)

if user_type == "Student":
    st.title("💡 Pocket Mentor")
    if protocol_context:
        st.error(f"🚨 Protocol Active: {protocol_context}")
    else:
        st.caption(f"Tactical advice for {st.session_state.get('study_stream', 'Students')}.")
else:
    st.title("💡 Strategic Protocols")
    if protocol_context:
        st.error(f"🚨 Protocol Active: {protocol_context}")
    else:
        st.caption("Livelihood defense & asset optimization.")

st.divider()

# ==========================================
# 3. TOPIC SELECTION (Auto vs Manual)
# ==========================================


if protocol_context:
    selected_topic = protocol_context
    st.info(f"The Sentinel has detected a specific threat: **{protocol_context}**. Generating counter-measures.")
    
    # Button to clear protocol and go back to normal
    if st.button("Cancel Protocol & Browse Topics"):
        st.session_state.pop("advice_topic_context", None)
        st.rerun()


else:
    if user_type == "Student":
        topics = [
            "💸 Stretching the Budget (Survival Mode)", 
            "🎓 Career & Internships (Stream Specific)", 
            "🍔 Food Hacks (Cheap Nutrition)", 
            "🍻 Social Life on a Budget"
        ]
        btn_label = "⚡ Ask Mentor"
    else:
        topics = [
            "⛽ Inflation Proofing", 
            "📉 Market Crash Defense", 
            "💳 Debt Clearance Strategy", 
            "🏰 Asset Allocation"
        ]
        btn_label = "🛡️ Generate Strategy"
        
    selected_topic = st.selectbox("Select Area of Concern:", topics)

# ==========================================
# 4. CONTEXT PACKAGING
# ==========================================


if user_type == "Student":
    wallet = st.session_state.get("savings_buffer", 0)
    limit = st.session_state.get("daily_limit", 100)
    stream = st.session_state.get("study_stream", "General")
    
    ai_prompt = (
        f"Student Profile: Stream: {stream}. Wallet Balance: ₹{wallet}. Daily Limit: ₹{limit}. "
        f"My current problem/topic is: '{selected_topic}'. "
        "Give me specific, actionable advice for this situation."
    )
    persona = "Student"

else:
    income = st.session_state.get("monthly_income", 0)
    burn = st.session_state.get("burn", 0)
    runway = st.session_state.get("runway_days", 0)
    risk = st.session_state.get("risk_score", 0)
    assets = st.session_state.get("held_assets", [])
    
    ai_prompt = (
        f"Financial Profile: Income: ₹{income}. Burn Rate: ₹{burn}. Runway: {runway} days. "
        f"Risk Score: {risk}/100. Assets: {assets}. "
        f"I need a strategic plan for: '{selected_topic}'. "
        "Focus on protecting my livelihood."
    )
    persona = "Standard"

# ==========================================
# 5. ACTION & DISPLAY
# ==========================================

with st.container(border=True):
    st.markdown("### AI Analysis Center")
    
    
    final_btn_label = f"🚨 Generate Protocol for {selected_topic}" if protocol_context else btn_label
    
    if st.button(final_btn_label, type="primary", use_container_width=True):
        
        with st.status("🔄 Sentinel is analyzing parameters...", expanded=True) as status:
            if user_type == "Student":
                st.write("Scanning wallet constraints...")
            else:
                st.write("Checking financial vitals...")
            
            time.sleep(0.5)
            st.write("Consulting knowledge base...")
            
            # THE API CALL
            advice_result = get_gemini_advice(ai_prompt, persona)
            
            status.update(label="Analysis Complete", state="complete", expanded=False)
        
        
        if "Traffic Overload" in advice_result:
             st.warning(advice_result, icon="⏳")
        elif "Connection Error" in advice_result:
             st.error(advice_result, icon="❌")
        else:
             st.success("Protocol Generated")
             st.markdown(advice_result)
             
             # Save to history so it doesn't vanish
             st.session_state["last_advice"] = advice_result
             st.session_state["last_advice_topic"] = selected_topic

# History Display
if "last_advice" in st.session_state and not protocol_context:
    st.divider()
    st.caption(f"Previously generated for: {st.session_state.get('last_advice_topic', 'Unknown')}")
    with st.container(border=True):
        st.markdown(st.session_state["last_advice"])
        if st.button("Clear History"):
            del st.session_state["last_advice"]
            st.rerun()