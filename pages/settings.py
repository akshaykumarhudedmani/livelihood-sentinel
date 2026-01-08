import streamlit as st

# ---- Auth gate ----
if not st.session_state.get("logged_in", False):
    st.warning("Please login as demo to continue.")
    st.stop()

st.title("⚙️ Settings")
st.caption("Language + Reset demo state")
st.divider()

# ---- Firebase connectivity (non-blocking) ----
try:
    from firestore_db import get_db

    db = get_db()
    db.collection("debug").document("streamlit_app_ok").set({"ok": True})
    st.success("Firebase connected ✅")
except Exception as e:
    st.warning("Firebase not connected (ok for local demo).")
    st.caption(f"Debug: {e}")

st.divider()

# ---- Language (read-only here) ----
st.subheader("Language")
st.write(f"Current language: **{st.session_state.get('lang', 'English')}**")
st.caption("Change language from the sidebar dropdown (top-left).")

st.write("")
st.subheader("Reset / Logout")

with st.container(border=True):
    st.write("Use this if you want to restart the demo from scratch.")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Reset demo (clear profile + alerts)", use_container_width=True):
            # FIXED: Added all new keys to ensure a full clean reset
            keys_to_clear = [
                "profile_complete",
                "monthly_income",
                "savings_buffer",
                "rent",
                "food",
                "transport",
                "utilities",
                "education",
                "medical",
                "emi_total",
                "burn",
                "net_savings",
                "runway_days",
                "risk_score",
                "alerts",
                "resolved_alert_ids",
                "voice_selected_alert_id",
                "voice_script",
                # New keys added below
                "crops_grown",
                "held_assets",
                "livelihood_sources",
                "assets",
                "alert_channels",
                "local_language",
                "fixed_monthly",
                "gig_avg_monthly",
                "farm_avg_monthly",
                "business_avg_monthly",
                "crop_input_cost",
                "sip",
                "portfolio_value"
            ]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            st.rerun()

    with c2:
        if st.button("Logout (clear everything)", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()