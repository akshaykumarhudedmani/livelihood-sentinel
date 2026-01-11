import streamlit as st


st.set_page_config(
    page_title="Livelihood Sentinel",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("lang", "English")
st.session_state.setdefault("profile_complete", False)


st.session_state.setdefault("alerts", [])
st.session_state.setdefault("resolved_alert_ids", set())
st.session_state.setdefault("voice_selected_alert_id", None)


LANGS = ["English", "Kannada", "Hindi"]
st.sidebar.selectbox("Language", LANGS, key="lang")

if st.session_state["lang"] != "English":
    st.sidebar.info(
        "Kannada/Hindi UI is coming soon. For now, the app is available in English.",
        icon="ℹ️",
    )


login_page = st.Page(
    "pages/login.py",
    title="Demo Login",
    icon=":material/login:",
    url_path="login",
)

home_page = st.Page(
    "pages/home.py",
    title="Home",
    icon=":material/home:",
    url_path="home",
)

tracking_page = st.Page(
    "pages/tracking.py",
    title="Tracking",
    icon=":material/account_balance_wallet:",
    url_path="tracking",
)

alerts_page = st.Page(
    "pages/news_alerts.py",
    title="News & Alerts",
    icon=":material/crisis_alert:",
    url_path="alerts",
)

advice_page = st.Page(
    "pages/advice.py",
    title="Advice",
    icon=":material/psychology:",
    url_path="advice",
)

voice_page = st.Page(
    "pages/voice.py",
    title="Voice",
    icon=":material/record_voice_over:",
    url_path="voice",
)

settings_page = st.Page(
    "pages/settings.py",
    title="Settings",
    icon=":material/settings:",
    url_path="settings",
)


if st.session_state["logged_in"]:
    pg = st.navigation(
        {
            "Livelihood Sentinel": [
                home_page,
                tracking_page,
                alerts_page,
                advice_page,
                voice_page,
                settings_page,
            ]
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()
