import streamlit as st
import pandas as pd
from src.theme import apply_theme
from src.theme import data_attribution
from src.database import get_all_thresholds, update_threshold, get_audit_log

st.set_page_config(page_title="Governance - FloodGuard AI", layout="wide", page_icon="🌊")
apply_theme()

st.title("Governance")

tab1, tab2 = st.tabs(["⚙️ Thresholds", "📋 Audit Log"])

with tab1:
    st.markdown("### Station Thresholds")
    st.caption("Thresholds are derived from historical percentiles (70th/90th/97th). Edit cautiously — changes are logged.")

    thresholds_df = get_all_thresholds()

    edited_df = st.data_editor(
        thresholds_df[["station_name", "watch_threshold", "warning_threshold", "danger_threshold"]],
        width="stretch",
        hide_index=True,
        disabled=["station_name"],
        key="threshold_editor"
    )

    operator_name = st.text_input("Your name (required to save changes)")

    if st.button("Save Changes"):
        # Rule: watch <= warning <= danger hona chahiye (khaali/NaN cell bhi invalid maani jayegi)
        is_valid = (
            (edited_df["watch_threshold"] <= edited_df["warning_threshold"])
            & (edited_df["warning_threshold"] <= edited_df["danger_threshold"])
        )
        invalid_stations = edited_df.loc[~is_valid, "station_name"].tolist()

        if not operator_name:
            st.error("Please enter your name before saving.")
        elif invalid_stations:
            st.error(
                "Thresholds must follow: watch ≤ warning ≤ danger. "
                "Nothing was saved. Please fix: " + ", ".join(invalid_stations)
            )
        else:
            changes = 0
            for _, row in edited_df.iterrows():
                original = thresholds_df[thresholds_df["station_name"] == row["station_name"]].iloc[0]
                if (row["watch_threshold"] != original["watch_threshold"] or
                        row["warning_threshold"] != original["warning_threshold"] or
                        row["danger_threshold"] != original["danger_threshold"]):
                    update_threshold(
                        row["station_name"], row["watch_threshold"],
                        row["warning_threshold"], row["danger_threshold"], operator_name
                    )
                    changes += 1

            if changes > 0:
                st.success(f"Saved {changes} threshold change(s).")
                st.cache_data.clear()
                st.rerun()
            else:
                st.info("No changes detected.")

with tab2:
    st.markdown("### Audit Log")
    st.caption("Last 50 recorded actions across the system.")

    audit_df = get_audit_log()
    st.dataframe(audit_df, width="stretch", hide_index=True)
    
data_attribution()