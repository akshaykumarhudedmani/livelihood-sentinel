import streamlit as st
import xml.etree.ElementTree as ET
from urllib.request import urlopen, Request
import requests
import json
import os

st.set_page_config(page_title="News & Alerts", page_icon=":material/crisis_alert:")

# ---- Auth gate ----
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

st.title("📰 News & Alerts")
st.caption("Official headlines filtered by your profile.")
st.divider()

# ---- GEMINI INTEGRATION (Real) ----
def ask_gemini_analysis(news_title, news_summary):
    """
    Sends context to Gemini 1.5 Flash for risk check.
    """
    api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return "⚠️ Error: GEMINI_API_KEY not found. Please add it to secrets."

    prompt_text = (
        f"You are a financial risk guard for a gig worker in India. "
        f"Analyze this news alert:\n"
        f"Title: {news_title}\n"
        f"Context: {news_summary}\n\n"
        f"Task: In 2 short bullet points, explain specifically how this affects their daily cash flow. "
        f"Keep it simple, urgent, and direct. No preamble."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"Gemini API Error: {response.status_code}"
    except Exception as e:
        return f"Connection Error: {e}"

# ---- Profile Gate & Data Load ----
if not st.session_state.get("profile_complete", False):
    st.info("Setup your tracking profile first to get alerts.")
    if st.button("Go to Tracking"):
        st.switch_page("pages/tracking.py")
    st.stop()

# Read session vars
income = int(st.session_state.get("monthly_income", 0))
transport = int(st.session_state.get("transport", 0))
emi_total = int(st.session_state.get("emi_total", 0))
burn = int(st.session_state.get("burn", 0))
runway_days = int(st.session_state.get("runway_days", 0))

crops = st.session_state.get("crops_grown", [])
held_assets = st.session_state.get("held_assets", [])

# Logic: Do they invest?
has_market_exposure = any(x in held_assets for x in ["Stocks / Mutual Funds", "Gold", "Crypto (BTC/ETH)"])

# Ensure resolved set exists
st.session_state.setdefault("resolved_alert_ids", set())


# ---- RSS Fetcher (Cached) ----
@st.cache_data(ttl=600)
def fetch_rss_items(url: str, limit: int = 3, timeout: int = 10):
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            if title:
                items.append({"title": title, "link": link, "pubDate": pub_date})
        return items
    except:
        return []

# -----------------------------
# Section A: Official Headlines (Smart Layout)
# -----------------------------
st.subheader("✅ Official Headlines")

sebi_feed = "https://www.sebi.gov.in/sebirss.xml"
rbi_press_feed = "https://www.rbi.org.in/pressreleases_rss.xml"
rbi_notif_feed = "https://www.rbi.org.in/notifications_rss.xml"

# LAYOUT LOGIC:
# If user has market assets -> Show 2 columns (SEBI + RBI)
# If user has NO market assets -> Show 1 column (RBI only)

if has_market_exposure:
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("SEBI (Market)")
            sebi_items = fetch_rss_items(sebi_feed, limit=3)
            if sebi_items:
                for it in sebi_items:
                    st.markdown(f"- [{it['title']}]({it['link']})")
            else:
                st.caption("No new updates.")
    
    with col2:
        with st.container(border=True):
            st.subheader("RBI (Economy)")
            rbi_items = fetch_rss_items(rbi_press_feed, limit=2)
            if rbi_items:
                for it in rbi_items:
                    st.markdown(f"- [{it['title']}]({it['link']})")
            else:
                st.caption("No new updates.")
else:
    # Single column layout for non-investors
    with st.container(border=True):
        st.subheader("RBI (Economy & Banking)")
        st.caption("Official updates affecting inflation and loans.")
        rbi_items = fetch_rss_items(rbi_press_feed, limit=3)
        if rbi_items:
            for it in rbi_items:
                st.markdown(f"- [{it['title']}]({it['link']})")
        else:
            st.caption("No new updates.")

st.divider()

# -----------------------------------
# Section B: Crops (Conditional)
# -----------------------------------
# ONLY show if user grows crops
if crops:
    st.subheader("🌾 Crops & Weather")
    st.caption(f"Tracking: {', '.join(crops)}")

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("Mandi Prices")
            st.caption("Official Agmarknet Source")
            st.write("Check daily arrivals and modal prices for your crops.")
            st.link_button("Open Agmarknet Portal", "https://agmarknet.gov.in", use_container_width=True)
    with c2:
        with st.container(border=True):
            st.subheader("Weather Alerts")
            st.caption("Official NDMA/IMD Source")
            st.write("Check heatwave/rainfall warnings in your district.")
            st.link_button("Open SACHET Portal", "https://sachet.ndma.gov.in", use_container_width=True)
    
    st.divider()

# --------------------------------
# Section C: Personal Impact Alerts
# --------------------------------
st.subheader("⚠️ Scenario Impact Analysis")

def compute_urgency(alert_id: str, level: str):
    # Base urgency
    urgency_label, urgency_color = ("Monitor", "yellow")

    # Critical runway override
    if runway_days and runway_days <= 7:
        return ("Immediate (0–48 hrs)", "red")

    if alert_id == "fuel_spike":
        urgency_label, urgency_color = ("Upcoming (3–7 days)", "orange")
    elif alert_id == "rate_hike":
        urgency_label, urgency_color = ("Upcoming (3–7 days)", "orange")
        if emi_total > 0:
            urgency_label, urgency_color = ("Immediate (0–48 hrs)", "red")
    
    return (urgency_label, urgency_color)

def build_impact_alerts():
    alerts = []

    # 1. Fuel Spike (Only if they have transport costs)
    if transport > 0:
        petrol_hike_perc = 0.10
        petrol_impact = int(transport * petrol_hike_perc)
        runway_hit = max(0, int((petrol_impact / (burn / 30)) if burn > 0 else 0))
        urg_label, urg_color = compute_urgency("fuel_spike", "WARNING")
        
        alerts.append({
            "id": "fuel_spike",
            "level": "WARNING",
            "icon": "⛽",
            "title": "Fuel price spike (impact)",
            "summary": f"Estimated +₹{petrol_impact:,}/month on your transport budget.",
            "impact_lines": [
                f"Your Transport Budget: ₹{transport:,}",
                f"Estimated Increase: ₹{petrol_impact:,}/month",
                f"Runway impact: -{runway_hit} day(s)",
            ],
            "actions": ["Carpool/Public Transport", "Hard cap on fuel spend"],
            "urgency_label": urg_label,
            "urgency_color": urg_color,
        })

    # 2. Rate Hike (Only if they have loans)
    if emi_total > 0:
        rate_hike_perc = 0.06
        emi_impact = int(emi_total * rate_hike_perc)
        urg_label, urg_color = compute_urgency("rate_hike", "WARNING")

        alerts.append({
            "id": "rate_hike",
            "level": "WARNING",
            "icon": "🏦",
            "title": "Interest rate hike (impact)",
            "summary": f"Possible EMI increase of ~₹{emi_impact:,}/month.",
            "impact_lines": [
                f"Current EMIs: ₹{emi_total:,}/month",
                f"Projected Increase: ₹{emi_impact:,}",
            ],
            "actions": ["Check Fixed-Rate options", "Prepay 5% principal"],
            "urgency_label": urg_label,
            "urgency_color": urg_color,
        })

    # 3. Inflation (Everyone sees this)
    inflation_hit = int(max(0, income * 0.02))
    level = "ADVISORY" if inflation_hit < 800 else "WARNING"
    urg_label, urg_color = compute_urgency("inflation", level)

    alerts.append({
        "id": "inflation",
        "level": level,
        "icon": "🛒",
        "title": "Cost-of-living pressure",
        "summary": f"Inflation may increase monthly costs by ~₹{inflation_hit:,}.",
        "impact_lines": [
            f"Estimated impact: ₹{inflation_hit:,}/month",
            "Tip: Lock essentials budget early.",
        ],
        "actions": ["Bulk buy staples", "Avoid impulse spending"],
        "urgency_label": urg_label,
        "urgency_color": urg_color,
    })

    # 4. Crops (Only if they grow crops)
    if crops:
        crop_input_cost = int(st.session_state.get("crop_input_cost", 0) or 0)
        crop_shock = int(max(0, crop_input_cost * 0.12))
        level = "WARNING" if crop_shock > 500 else "ADVISORY"
        urg_label, urg_color = compute_urgency("farm_inputs", level)

        alerts.append({
            "id": "farm_inputs",
            "level": level,
            "icon": "🌾",
            "title": "Farm input cost shock",
            "summary": f"Possible +₹{crop_shock:,}/month on inputs (demo).",
            "impact_lines": [
                f"Crops: {', '.join(crops)}",
                f"Input Cost Risk: ₹{crop_shock:,}",
            ],
            "actions": ["Buy inputs early", "Compare 2 suppliers"],
            "urgency_label": urg_label,
            "urgency_color": urg_color,
        })

    return alerts


impact_alerts = build_impact_alerts()
st.session_state["alerts"] = impact_alerts

# ---- Alert Render Logic ----
# Controls
c1, c2, c3 = st.columns([1.2, 1.2, 2.6])
with c1:
    show_resolved = st.checkbox("Show resolved", value=False)
with c2:
    if st.button("Clear resolved history"):
        st.session_state["resolved_alert_ids"] = set()
        st.rerun()

# Tabs
tab_warning, tab_advisory, tab_critical = st.tabs(["Warning", "Advisory", "Critical"])

def render_alert_card(a, tab_prefix: str, idx: int):
    sev_badge = {"CRITICAL": "🔴", "WARNING": "🟡", "ADVISORY": "🟢"}.get(a["level"], "⚪")

    with st.container(border=True):
        st.subheader(f"{sev_badge} {a['icon']} {a['title']}")
        st.badge(a.get("urgency_label", "Monitor"), color=a.get("urgency_color", "yellow"))
        st.write(a["summary"])

        with st.expander("Show impact details"):
            for line in a["impact_lines"]:
                st.write(f"• {line}")
            
            st.divider()
            st.caption("AI Analysis Tool")
            
            # GEMINI BUTTON
            gemini_key = f"gemini_result_{a['id']}"
            if st.button("✨ Analyze with Gemini", key=f"btn_gemini_{tab_prefix}_{idx}"):
                with st.spinner("Gemini is analyzing risks..."):
                    result = ask_gemini_analysis(a['title'], a['summary'])
                    st.session_state[gemini_key] = result
            
            if gemini_key in st.session_state:
                st.info(st.session_state[gemini_key])

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Mark resolved", use_container_width=True, key=f"{tab_prefix}_{idx}_resolve_{a['id']}"):
                st.session_state["resolved_alert_ids"].add(a["id"])
                st.toast(f"Resolved: {a['title']}") # <--- UI POLISH: TOAST MESSAGE
                st.rerun()
        with c2:
            if st.button("🎙️ Listen", use_container_width=True, key=f"{tab_prefix}_{idx}_listen_{a['id']}"):
                st.session_state["voice_selected_alert_id"] = a["id"]
                st.switch_page("pages/voice.py")

def render_filtered(level: str, tab_prefix: str):
    found = False
    for idx, a in enumerate(impact_alerts):
        if a["level"] != level:
            continue
        is_resolved = a["id"] in st.session_state["resolved_alert_ids"]
        if is_resolved and not show_resolved:
            continue
        render_alert_card(a, tab_prefix=tab_prefix, idx=idx)
        found = True
    if not found:
        st.info("No active alerts in this category.")

with tab_warning: render_filtered("WARNING", "warning")
with tab_advisory: render_filtered("ADVISORY", "advisory")
with tab_critical: render_filtered("CRITICAL", "critical")