import streamlit as st
import time

st.set_page_config(page_title="Tracking", page_icon=":material/account_balance_wallet:")

# ==========================================
# 0. AUTH CHECK
# ==========================================
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

st.title("💰 Tracking Setup")
st.caption("Configure your profile to activate the Sentinel.")

# ==========================================
# 1. THE MAIN SWITCH
# ==========================================
user_type = st.radio(
    "Select your Profile Type:",
    ["🌾 Standard (Family/Farm/Business)", "🎓 Student (Pocket Money)"],
    index=0 if st.session_state.get("user_type") != "Student" else 1,
    horizontal=True,
    help="Choose 'Standard' for full household/business tracking. Choose 'Student' for allowance & pocket money tracking."
)

st.divider()

# ==========================================
# 2. LOGIC FUNCTIONS
# ==========================================
def compute_standard_stats(income, rent, food, transport, utilities, emi, savings):
    burn = rent + food + transport + utilities + emi + st.session_state.get("education", 0) + st.session_state.get("medical", 0)
    net_savings = income - burn
    daily_burn = burn / 30 if burn > 0 else 0
    
    if daily_burn > 0:
        runway_days = int(savings / daily_burn)
    else:
        runway_days = 999 

    risk = 50
    if net_savings < 0: risk += 25
    if emi > 0.35 * income and income > 0: risk += 15
    risk = max(0, min(100, risk))
    
    return burn, net_savings, runway_days, risk

def compute_student_stats(wallet_balance, daily_limit):
    projected_burn = daily_limit * 30
    if daily_limit > 0:
        runway_days = int(wallet_balance / daily_limit)
    else:
        runway_days = 999
        
    risk = 0
    if runway_days < 7: risk = 90
    elif runway_days < 15: risk = 60
    elif runway_days < 30: risk = 30
    
    return projected_burn, runway_days, risk

# ==========================================
# 3. PROFILE SETUP (REACTIVE - NO FORM)
# ==========================================

# ---------------------------------------------------------
# OPTION A: STANDARD SETUP (Family/Farm/Business)
# ---------------------------------------------------------
if "Standard" in user_type:
    st.subheader("Step 1: Income Sources")
    
    # 1. Source Selection (Instant Update)
    livelihood_sources = st.multiselect(
        "How do you earn?",
        options=[
            "Fixed income (Salary/Pension)",
            "Variable/Gig income (Freelance/Driver)",
            "Production-based (Farming/Business)",
            "Investment income (Stocks/Rent)",
        ],
        default=st.session_state.get("livelihood_sources", ["Fixed income (Salary/Pension)"]),
    )

    # 2. Smart Inputs (Conditional Visibility)
    fixed_monthly = 0
    if "Fixed income (Salary/Pension)" in livelihood_sources:
        fixed_monthly = st.number_input("Monthly Salary/Pension (₹)", min_value=0, step=500, value=int(st.session_state.get("fixed_monthly", 25000)))

    gig_avg_monthly = 0
    if "Variable/Gig income (Freelance/Driver)" in livelihood_sources:
        gig_avg_monthly = st.number_input("Avg. Gig Income (₹)", min_value=0, step=500, value=int(st.session_state.get("gig_avg_monthly", 0)))

    farm_avg_monthly = 0
    crop_input_cost = 0
    production_type = "N/A"
    crops_grown = []

    # Only ask production details if selected
    if "Production-based (Farming/Business)" in livelihood_sources:
        st.markdown("---")
        st.caption("🏭 Production / Farming Details")
        
        c_prod1, c_prod2 = st.columns(2)
        with c_prod1:
            production_type = st.selectbox("Type", ["Farming", "Shop/Business", "Dairy"], index=0)
        with c_prod2:
            farm_avg_monthly = st.number_input("Avg. Monthly Revenue (₹)", min_value=0, step=500, value=int(st.session_state.get("farm_avg_monthly", 0)))
        
        # SMART HIDDEN: Input Costs
        crop_input_cost = st.number_input("Input Costs (Seeds/Stock) (₹)", min_value=0, step=500, value=int(st.session_state.get("crop_input_cost", 0)))
        
        # SMART HIDDEN: Crops only if farming
        if production_type == "Farming":
            crops_grown = st.multiselect(
                "Crops Grown (for Weather Alerts)",
                ["Onion", "Rice", "Cotton", "Wheat", "Tomato", "Sugarcane"],
                default=st.session_state.get("crops_grown", [])
            )

    sip = 0
    held_assets = []
    # Only ask Investment details if selected
    if "Investment income (Stocks/Rent)" in livelihood_sources:
        st.markdown("---")
        st.caption("📈 Investment Details")
        sip = st.number_input("Monthly SIP/Investment (₹)", min_value=0, step=500, value=int(st.session_state.get("sip", 0)))
        
        # SMART HIDDEN: Holdings
        held_assets = st.multiselect(
            "Portfolio Assets (for Market News)",
            ["Stocks", "Mutual Funds", "Gold", "Crypto", "Real Estate"],
            default=st.session_state.get("held_assets", [])
        )

    st.divider()
    st.subheader("Step 2: Core Expenses")
    
    # Auto-sum income
    total_income = fixed_monthly + gig_avg_monthly + farm_avg_monthly
    monthly_income = st.number_input("Total Monthly Income (₹)", value=int(total_income))
    
    c1, c2 = st.columns(2)
    with c1:
        rent = st.number_input("Rent (₹)", value=int(st.session_state.get("rent", 8000)))
        food = st.number_input("Food (₹)", value=int(st.session_state.get("food", 5000)))
        utilities = st.number_input("Utilities (₹)", value=int(st.session_state.get("utilities", 1500)))
    with c2:
        transport = st.number_input("Transport (₹)", value=int(st.session_state.get("transport", 2000)))
        emi_total = st.number_input("Loan EMIs (₹)", value=int(st.session_state.get("emi_total", 0)))
        savings_buffer = st.number_input("Current Savings/Cash (₹)", value=int(st.session_state.get("savings_buffer", 20000)))

# ---------------------------------------------------------
# OPTION B: STUDENT SETUP (Pocket Money)
# ---------------------------------------------------------
else:
    st.subheader("🎓 Student Identity")
    
    college_options = [
        "Amity University, Bengaluru", 
        "Christ University", 
        "Jain University", 
        "PES University", 
        "Other"
    ]
    college_name = st.selectbox(
        "College / University", 
        options=college_options,
        index=0
    )
    
    study_stream = st.selectbox(
        "Study Stream (For Career News)",
        ["CSE / Tech", "Finance / Commerce", "Medical / Biology", "Arts / Humanities", "Law", "Architecture", "Management (BBA/MBA)"],
        index=0
    )
    
    st.divider()
    st.subheader("💰 Pocket Money Reality")
    
    student_allowance = st.number_input(
        "Monthly Allowance Received (₹)", 
        min_value=0, step=100, 
        value=int(st.session_state.get("monthly_income", 5000))
    )
    
    current_wallet = st.number_input(
        "Current Money in Wallet/UPI (₹)", 
        min_value=0, step=50, 
        value=int(st.session_state.get("savings_buffer", 500))
    )
    
    daily_limit = st.number_input(
        "Daily Spending Limit (₹)", 
        min_value=10, step=10, 
        value=int(st.session_state.get("daily_limit", 150))
    )
    
    # Defaults for student to avoid errors
    rent, food, transport, utilities, emi_total = 0, 0, 0, 0, 0
    livelihood_sources = ["Student Allowance"]
    crops_grown, held_assets = [], []
    fixed_monthly, gig_avg_monthly, farm_avg_monthly = 0, 0, 0
    production_type = "N/A"
    crop_input_cost, sip = 0, 0
    monthly_income = student_allowance
    savings_buffer = current_wallet

st.divider()

# Language Selection (Common)
alert_channels = st.multiselect("Alerts", ["Text", "Voice"], default=["Text"])

# ==========================================
# 4. SAVE LOGIC (ACTION BUTTON)
# ==========================================
if st.button("🚀 Activate Sentinel", type="primary", use_container_width=True):
    
    # A. The Loading Effect
    with st.status("🔄 Configuring Sentinel Core...", expanded=True) as status:
        if "Student" in user_type:
            st.write("Calibrating Student Budget...")
            time.sleep(0.6)
            st.write(f"Setting Campus Focus: {college_name}...")
        else:
            st.write("Analyzing Livelihood Risks...")
            time.sleep(0.6)
            st.write("Connecting to Market Feeds...")
            
        time.sleep(0.5)
        st.write("Saving Profile Encrypted...")
        status.update(label="✅ Setup Complete!", state="complete", expanded=False)

    # B. Save to Session State
    if "Student" in user_type:
        st.session_state["user_type"] = "Student"
        st.session_state["college_name"] = college_name
        st.session_state["study_stream"] = study_stream
        st.session_state["monthly_income"] = student_allowance
        st.session_state["savings_buffer"] = current_wallet 
        st.session_state["daily_limit"] = daily_limit
        st.session_state["rent"] = 0
        st.session_state["food"] = 0
        st.session_state["emi_total"] = 0
        st.session_state["transport"] = 0
        
        burn, runway, risk = compute_student_stats(current_wallet, daily_limit)
        
    else:
        st.session_state["user_type"] = "Standard"
        st.session_state["livelihood_sources"] = livelihood_sources
        st.session_state["fixed_monthly"] = fixed_monthly
        st.session_state["gig_avg_monthly"] = gig_avg_monthly
        st.session_state["farm_avg_monthly"] = farm_avg_monthly
        st.session_state["production_type"] = production_type
        st.session_state["crop_input_cost"] = crop_input_cost
        st.session_state["crops_grown"] = crops_grown
        st.session_state["held_assets"] = held_assets
        st.session_state["sip"] = sip
        
        st.session_state["monthly_income"] = monthly_income
        st.session_state["savings_buffer"] = savings_buffer
        st.session_state["rent"] = rent
        st.session_state["food"] = food
        st.session_state["transport"] = transport
        st.session_state["utilities"] = utilities
        st.session_state["emi_total"] = emi_total
        
        burn, net_savings, runway, risk = compute_standard_stats(
            monthly_income, rent, food, transport, utilities, emi_total, savings_buffer
        )
        st.session_state["net_savings"] = net_savings

    # Common Saves
    st.session_state["burn"] = burn
    st.session_state["runway_days"] = runway
    st.session_state["risk_score"] = risk
    st.session_state["profile_complete"] = True
    
    # C. Persist to DB
    from db_ops import save_profile
    
    profile_data = {
        "user_type": st.session_state["user_type"],
        "monthly_income": st.session_state["monthly_income"],
        "burn": st.session_state["burn"],
        "runway_days": st.session_state["runway_days"],
        "savings_buffer": st.session_state["savings_buffer"],
    }
    
    if st.session_state["user_type"] == "Student":
        profile_data.update({
            "college_name": st.session_state["college_name"],
            "study_stream": st.session_state["study_stream"],
            "daily_limit": st.session_state["daily_limit"]
        })
    else:
        profile_data.update({
            "crops_grown": st.session_state["crops_grown"],
            "held_assets": st.session_state["held_assets"],
            "emi_total": st.session_state["emi_total"]
        })

    save_profile(profile_data)

    st.success(f"Sentinel active in {st.session_state['user_type']} Mode.")
    time.sleep(1)
    st.switch_page("pages/home.py")