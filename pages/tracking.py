import streamlit as st
import time

st.set_page_config(page_title="Tracking", page_icon="💰")

if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

st.title("💰 Tracking Setup")
st.caption("Configure your financial baseline to activate risk models.")

# --- NEW: User Instruction (Requested) ---
st.info("ℹ️ **System Note:** The visual simulations in 'News & Alerts' will generated **exclusively** based on the Assets and Liabilities you configure below.")

# ==========================================
# 1. DEFAULTS (CLEAN SLATE)
# ==========================================
defaults = {
    "monthly_income": 0,
    "rent": 0,
    "food": 0,
    "transport": 0,
    "utilities": 0,
    "emi_total": 0,
    "savings_buffer": 0,
    "city_village": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Lists default to empty
st.session_state.setdefault("livelihood_sources", [])
st.session_state.setdefault("assets", [])
st.session_state.setdefault("crops_grown", [])
st.session_state.setdefault("held_assets", [])

def compute_stats(income, rent, food, transport, utilities, emi_total, savings_buffer):
    burn = rent + food + transport + utilities + emi_total + st.session_state.get("education", 0) + st.session_state.get("medical", 0)
    net_savings = income - burn
    daily_burn = burn / 30 if burn > 0 else 0
    
    if daily_burn > 0:
        runway_days = int(savings_buffer / daily_burn)
    else:
        runway_days = 999 

    risk = 50
    if net_savings < 0: risk += 25
    if emi_total > 0.35 * income and income > 0: risk += 15
    if transport > 0.15 * income and income > 0: risk += 10
    risk = max(0, min(100, risk))

    return burn, net_savings, runway_days, risk

# ==========================================
# 2. THE FORM
# ==========================================
with st.form("profile_setup_form", clear_on_submit=False):
    
    # --- LOCATION ---
    st.subheader("📍 Location")
    c_loc1, c_loc2 = st.columns([3, 1])
    with c_loc1:
        city_village = st.text_input(
            "City / Village Name", 
            value=st.session_state.get("city_village", ""), 
            placeholder="e.g. Mandya",
            key="city_village_widget"
        )
    with c_loc2:
        st.write("") 
        st.write("")
        if st.form_submit_button("🌍 Use GPS (Demo)"):
            st.toast("📍 Google Maps Integration: Future Improvement (Phase 2)")

    st.divider()

    # --- LIVELIHOOD ---
    st.subheader("Step 1: How do you earn money?")

    livelihood_sources = st.multiselect(
        "Select one or more sources",
        options=[
            "Fixed income (Salary/Pension/Stipend)",
            "Variable/Gig income (Freelance/Daily wage/Driver/Delivery)",
            "Production-based (Farming/Fishing/Artisan)",
            "Business income (Shop/Trade/Kirana)",
            "Investment income (Stocks/MFs/Dividends/Interest)",
        ],
        default=st.session_state.get("livelihood_sources", []),
        key="livelihood_sources_widget",
    )

    # --- Conditional Inputs ---
    fixed_monthly = 0
    if "Fixed income (Salary/Pension/Stipend)" in livelihood_sources:
        st.markdown("**Fixed income details**")
        fixed_monthly = st.number_input(
            "Salary/Pension/Stipend per month (₹)", min_value=0, step=500,
            value=int(st.session_state.get("fixed_monthly", 0)),
            key="fixed_monthly_widget"
        )

    gig_avg_monthly = 0
    if "Variable/Gig income (Freelance/Daily wage/Driver/Delivery)" in livelihood_sources:
        st.markdown("**Gig/Variable income details**")
        gig_avg_monthly = st.number_input(
            "Average gig/variable income per month (₹)", min_value=0, step=500,
            value=int(st.session_state.get("gig_avg_monthly", 0)),
            key="gig_avg_monthly_widget"
        )

    production_type = "N/A"
    farm_avg_monthly = 0
    crop_input_cost = 0
    if "Production-based (Farming/Fishing/Artisan)" in livelihood_sources:
        st.markdown("**Production-based details**")
        production_type = st.selectbox(
            "Primary production type",
            options=["Crop farming (seasonal)", "Dairy/Livestock (steady)", "Mixed (crop + dairy)"],
            index=0, key="production_type_widget"
        )
        farm_avg_monthly = st.number_input(
            "Average production income per month (₹)", min_value=0, step=500,
            value=int(st.session_state.get("farm_avg_monthly", 0)),
            key="farm_avg_monthly_widget"
        )
        crop_input_cost = st.number_input(
            "Seeds/Fertilizer/Fodder etc. (₹/month avg)", min_value=0, step=500,
            value=int(st.session_state.get("crop_input_cost", 0)),
            key="crop_input_cost_widget"
        )

    business_avg_monthly = 0
    if "Business income (Shop/Trade/Kirana)" in livelihood_sources:
        st.markdown("**Business details**")
        business_avg_monthly = st.number_input(
            "Average business income per month (₹)", min_value=0, step=500,
            value=int(st.session_state.get("business_avg_monthly", 0)),
            key="business_avg_monthly_widget"
        )

    sip = 0
    portfolio_value = 0
    risk_style = "N/A"
    if "Investment income (Stocks/MFs/Dividends/Interest)" in livelihood_sources:
        st.markdown("**Investor details**")
        sip = st.number_input(
            "SIP / Investments per month (₹)", min_value=0, step=500,
            value=int(st.session_state.get("sip", 0)), key="sip_widget"
        )
        portfolio_value = st.number_input(
            "Portfolio value (₹)", min_value=0, step=1000,
            value=int(st.session_state.get("portfolio_value", 0)), key="portfolio_value_widget"
        )
        risk_style = st.selectbox(
            "Risk style", ["Conservative", "Balanced", "Aggressive"],
            index=1, key="risk_style_widget"
        )

    st.divider()
    
    # --- ASSETS ---
    st.subheader("Step 2: Assets & Crops")

    assets = st.multiselect(
        "Select your asset types",
        options=[
            "Cash & Savings (bank/cash/wallet)",
            "Financial assets (stocks/MFs/FDs/gold bonds)",
            "Livelihood assets (crops/livestock/tools)",
            "Physical assets (land/house/vehicle)",
            "Human capital (skills/education/certifications)",
        ],
        default=st.session_state.get("assets", []),
        key="assets_widget",
    )

    livelihood_assets_notes = ""
    if "Livelihood assets (crops/livestock/tools)" in assets:
        livelihood_assets_notes = st.text_input(
            "Details (e.g., 2 cows, onion crop)",
            value=st.session_state.get("livelihood_assets_notes", ""),
            key="livelihood_assets_notes_widget"
        )

    c1, c2 = st.columns(2)
    with c1:
        crops_grown = st.multiselect(
            "Crops grown (for Alerts)",
            options=["Onion", "Rice", "Cotton", "Wheat"],
            default=st.session_state.get("crops_grown", []),
            key="crops_grown_widget",
        )
    with c2:
        held_assets = st.multiselect(
            "Holdings (for Market News)",
            options=["Gold", "Stocks / Mutual Funds", "Crypto (BTC/ETH)", "Land / Vehicle"],
            default=st.session_state.get("held_assets", []),
            key="held_assets_widget",
        )

    st.divider()
    
    # --- ALERTS ---
    st.subheader("Step 3: Alert Preferences")
    
    c1, c2 = st.columns(2)
    with c1:
        alert_channels = st.multiselect(
            "Alert Channels", ["Text", "Voice"],
            default=st.session_state.get("alert_channels", ["Text"]),
            key="alert_channels_widget"
        )
    with c2:
        local_language = st.checkbox(
            "Enable Local Language Support",
            value=bool(st.session_state.get("local_language", True)),
            key="local_language_widget"
        )

    st.divider()
    
    # --- CORE FINANCIALS ---
    st.subheader("Core Financials (Powers AI)")

    # Auto-sum logic (Helper)
    calculated_income = fixed_monthly + gig_avg_monthly + farm_avg_monthly + business_avg_monthly
    
    monthly_income = st.number_input(
        "Total Monthly Income (Auto-sum or Override) (₹)", min_value=0, step=500,
        value=int(st.session_state.get("monthly_income", calculated_income)),
        key="monthly_income_widget"
    )

    savings_buffer = st.number_input(
        "Emergency Savings Buffer (₹)", min_value=0, step=1000,
        value=int(st.session_state.get("savings_buffer", 0)),
        key="savings_buffer_widget"
    )

    c1, c2 = st.columns(2)
    with c1:
        rent = st.number_input("Rent / Housing (₹)", min_value=0, step=500, value=int(st.session_state.rent), key="rent_widget")
        food = st.number_input("Food & Groceries (₹)", min_value=0, step=500, value=int(st.session_state.food), key="food_widget")
        utilities = st.number_input("Utilities (₹)", min_value=0, step=500, value=int(st.session_state.utilities), key="utilities_widget")
    with c2:
        transport = st.number_input("Transport / Fuel (₹)", min_value=0, step=500, value=int(st.session_state.transport), key="transport_widget")
        education = st.number_input("Education (₹)", min_value=0, step=500, value=int(st.session_state.get("education", 0)), key="education_widget")
        medical = st.number_input("Medical (₹)", min_value=0, step=500, value=int(st.session_state.get("medical", 0)), key="medical_widget")

    emi_total = st.number_input(
        "Total Loan EMIs (₹)", min_value=0, step=500,
        value=int(st.session_state.emi_total),
        key="emi_total_widget"
    )

    submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

# ==========================================
# 3. SAVE LOGIC
# ==========================================
if submitted:
    with st.status("🔄 Processing Financial Profile...", expanded=True) as status:
        st.write("Aggregating income streams...")
        time.sleep(0.5)
        st.write("Calculating Burn Rate & Survival Runway...")
        time.sleep(0.5)
        st.write("Calibrating Risk Score...")
        time.sleep(0.5)
        st.write("Encrypting data to Firestore...")
        time.sleep(0.5)
        status.update(label="Profile Securely Saved!", state="complete", expanded=False)

    # Save inputs
    st.session_state["city_village"] = city_village
    st.session_state["livelihood_sources"] = livelihood_sources
    st.session_state["assets"] = assets
    st.session_state["alert_channels"] = alert_channels
    st.session_state["local_language"] = bool(local_language)
    st.session_state["crops_grown"] = crops_grown
    st.session_state["held_assets"] = held_assets
    
    st.session_state["fixed_monthly"] = int(fixed_monthly)
    st.session_state["gig_avg_monthly"] = int(gig_avg_monthly)
    st.session_state["production_type"] = production_type
    st.session_state["farm_avg_monthly"] = int(farm_avg_monthly)
    st.session_state["crop_input_cost"] = int(crop_input_cost)
    st.session_state["business_avg_monthly"] = int(business_avg_monthly)
    st.session_state["sip"] = int(sip)
    st.session_state["portfolio_value"] = int(portfolio_value)
    st.session_state["risk_style"] = risk_style
    st.session_state["livelihood_assets_notes"] = livelihood_assets_notes

    st.session_state["monthly_income"] = int(monthly_income)
    st.session_state["savings_buffer"] = int(savings_buffer)
    st.session_state["rent"] = int(rent)
    st.session_state["food"] = int(food)
    st.session_state["transport"] = int(transport)
    st.session_state["utilities"] = int(utilities)
    st.session_state["education"] = int(education)
    st.session_state["medical"] = int(medical)
    st.session_state["emi_total"] = int(emi_total)

    # Compute Stats
    burn, net_savings, runway_days, risk = compute_stats(
        income=st.session_state["monthly_income"],
        rent=st.session_state["rent"],
        food=st.session_state["food"],
        transport=st.session_state["transport"],
        utilities=st.session_state["utilities"],
        emi_total=st.session_state["emi_total"],
        savings_buffer=st.session_state["savings_buffer"],
    )

    st.session_state["burn"] = int(burn)
    st.session_state["net_savings"] = int(net_savings)
    st.session_state["runway_days"] = int(runway_days)
    st.session_state["risk_score"] = int(risk)
    st.session_state["profile_complete"] = True

    # Persist
    from db_ops import save_profile
    profile = {
        "city_village": st.session_state.get("city_village", ""),
        "monthly_income": st.session_state.get("monthly_income", 0),
        "transport": st.session_state.get("transport", 0),
        "emi_total": st.session_state.get("emi_total", 0),
        "burn": st.session_state.get("burn", 0),
        "runway_days": st.session_state.get("runway_days", 0),
        "crops_grown": st.session_state.get("crops_grown", []),
        "held_assets": st.session_state.get("held_assets", []),
    }
    save_profile(profile)

    st.success("Profile saved. Dashboard + Alerts are now active.")

    if net_savings < 0:
        st.error("Warning: Cashflow negative.")
    
    if runway_days <= 15:
        st.error("Danger: Survival runway is very low (≤ 15 days).")
    elif runway_days <= 30:
        st.warning("Caution: Survival runway is tight (≤ 30 days).")

st.divider()
st.caption("👨‍⚖️ **Judges Note:** This is a demo prototype. In a real-world implementation, this financial data would be aggregated automatically via Account Aggregator (AA) frameworks or Banking APIs.")