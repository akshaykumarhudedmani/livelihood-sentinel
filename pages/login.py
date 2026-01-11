import streamlit as st

st.set_page_config(page_title="Demo Login", page_icon=":material/login:")


st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("lang", "English")


left, mid, right = st.columns([1, 3, 1])
with mid:
    try:
        st.image("assets/hero.jpeg", use_container_width=True)
    except Exception:
        st.caption("Missing image: assets/hero.jpeg")

st.write("")


st.markdown(
    "<h1 style='text-align:center; margin-bottom: 0.2rem;'>Livelihood Sentinel</h1>",
    unsafe_allow_html=True,
)


st.caption("Demo mode (no real authentication).")
st.write("")


if st.button("Login as Demo → Start", type="primary", use_container_width=True):
    st.session_state["logged_in"] = True
    st.rerun()

st.write("")
st.caption('"we track threats to your livelihood"')
