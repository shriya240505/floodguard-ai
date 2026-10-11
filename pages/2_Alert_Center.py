import streamlit as st
import pandas as pd
from src.theme import apply_theme, data_attribution
from src.auth import admin_login, is_admin
from src.database import get_open_alerts, acknowledge_alert, close_alert, sync_alerts
from models.predict import get_all_stations_status

st.set_page_config(page_title="Alert Center - FloodGuard AI", layout="wide", page_icon="🌊")
apply_theme()

st.title("Alert Center")

admin_login()
if not is_admin():
    st.info("View-only mode. Enter the admin password to acknowledge or close alerts.")


@st.cache_data(ttl=300)
def load_status():
    return get_all_stations_status()


with st.spinner("Checking stations..."):
    all_status = load_status()
    sync_alerts(all_status)

alerts_df = get_open_alerts()

if len(alerts_df) == 0:
    st.success("No open alerts. All stations within normal parameters.")
else:
    st.markdown(f"### {len(alerts_df)} Open Alert(s)")

    severity_filter = st.multiselect(
        "Filter by severity",
        options=["Danger", "Warning", "Watch"],
        default=["Danger", "Warning", "Watch"]
    )

    filtered_df = alerts_df[alerts_df["severity"].isin(severity_filter)]

    for _, alert in filtered_df.iterrows():
        with st.expander(f"{alert['severity']} — {alert['station_name']} ({alert['water_level']:.2f} m)"):
            st.write(f"**Opened at:** {alert['opened_at']}")
            st.write(f"**Status:** {alert['status']}")

            if pd.notna(alert["acknowledged_by"]):
                st.write(f"**Acknowledged by:** {alert['acknowledged_by']}")
                st.write(f"**Note:** {alert['notes']}")

            if not is_admin():
                st.caption("Admin login required to acknowledge or close this alert.")
                continue

            col1, col2 = st.columns(2)

            with col1:
                with st.form(key=f"ack_form_{alert['alert_id']}"):
                    operator_name = st.text_input("Your name", key=f"name_{alert['alert_id']}")
                    note = st.text_area("Note", key=f"note_{alert['alert_id']}")
                    submitted = st.form_submit_button("Acknowledge")

                    if submitted and operator_name:
                        acknowledge_alert(alert["alert_id"], operator_name, note)
                        st.success("Acknowledged")
                        st.rerun()

            with col2:
                if st.button("Close Alert", key=f"close_{alert['alert_id']}"):
                    close_alert(alert["alert_id"], "Operator")
                    st.success("Alert closed")
                    st.rerun()

data_attribution()