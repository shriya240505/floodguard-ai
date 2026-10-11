import hmac
import streamlit as st


def _expected_password():
    """Password sirf Streamlit Secrets se aata hai, code me kabhi nahi."""
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except Exception:
        return None


def is_admin():
    return bool(st.session_state.get("is_admin"))


def admin_login():
    """Page ke upar admin login box dikhata hai."""
    if is_admin():
        col1, col2 = st.columns([6, 1])
        col1.success("Admin mode is on.")
        if col2.button("Log out"):
            st.session_state["is_admin"] = False
            st.rerun()
        return

    with st.expander("🔒 Admin login"):
        password = st.text_input("Admin password", type="password", key="admin_password_input")
        if password:
            expected = _expected_password()
            if expected and hmac.compare_digest(password.encode(), str(expected).encode()):
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")