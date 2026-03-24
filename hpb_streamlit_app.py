#!/usr/bin/env python3
"""Streamlit app for Healthy 365 reward value exploration."""

from __future__ import annotations

import streamlit as st

from health_rewards_data import HealthInputs, build_health_reward_objects


CARD_CONFIG = {
    "activesg": {
        "title": "Gym Memberships, Facility Bookings",
        "image_url": "https://images.pexels.com/photos/416717/pexels-photo-416717.jpeg?auto=compress&cs=tinysrgb&w=1200",
    },
    "retail_vouchers": {
        "title": "Retail Vouchers, Boba, Commute Credits",
        "image_url": "https://images.pexels.com/photos/264636/pexels-photo-264636.jpeg?auto=compress&cs=tinysrgb&w=1200",
    },
    "health_insurance": {
        "title": "Health Insurance",
        "image_url": "https://images.pexels.com/photos/40568/medical-appointment-doctor-healthcare-40568.jpeg?auto=compress&cs=tinysrgb&w=1200",
    },
}


def _get_value_for_category(reward_table, category: str) -> float:
    matches = reward_table.loc[reward_table["category"] == category, "dollar_value"]
    return float(matches.iloc[0]) if not matches.empty else 0.0


def main() -> None:
    st.set_page_config(page_title="Healthy 365 Rewards Explorer", layout="wide")
    st.title("Healthy 365 Rewards Explorer")
    st.write("Adjust your weekly habits to estimate reward dollar value by period.")

    with st.sidebar:
        st.header("Inputs")
        daily_steps = st.number_input(
            "Daily step count",
            min_value=0,
            max_value=50000,
            value=7500,
            step=500,
        )
        daily_sleep_hours = st.number_input(
            "Sleep (hours)",
            min_value=0.0,
            max_value=24.0,
            value=7.0,
            step=0.1,
            format="%.1f",
        )
        weekly_exercise_minutes = st.number_input(
            "Exercise minutes per week",
            min_value=0,
            max_value=2000,
            value=90,
            step=10,
        )

    period_label = st.selectbox(
        "Display reward period",
        options=["Daily", "Weekly", "Yearly"],
        index=2,
    )
    period_key = period_label.lower().replace("ly", "")

    inputs = HealthInputs(
        daily_steps=int(daily_steps),
        daily_sleep_hours=float(daily_sleep_hours),
        weekly_exercise_minutes=int(weekly_exercise_minutes),
        has_health_screening=False,
    )
    result = build_health_reward_objects(inputs)
    reward_table = result["rewards_by_period"][period_key]

    cols = st.columns(3)
    ordered_categories = ["activesg", "retail_vouchers", "health_insurance"]

    for col, category in zip(cols, ordered_categories):
        info = CARD_CONFIG[category]
        with col:
            st.subheader(info["title"])
            st.image(info["image_url"], use_container_width=True)
            value = _get_value_for_category(reward_table, category)
            st.metric(label=f"{period_label} Dollar Value", value=f"${value:,.2f}")


if __name__ == "__main__":
    main()
