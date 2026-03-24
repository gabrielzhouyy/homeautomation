#!/usr/bin/env python3
"""Streamlit app for Healthy 365 reward value exploration."""

from __future__ import annotations

import streamlit as st

from hpb_data import HealthInputs, build_health_reward_objects


CARD_CONFIG = {
    "activesg": {
        "title": "ActiveSG",
        "description": "Gym memberships, facility bookings, and fitness classes.",
        "icon": "🏋️",
    },
    "retail_vouchers": {
        "title": "Retail",
        "description": "Retail vouchers, boba, commute credits.",
        "icon": "🛍️",
    },
    "health_insurance": {
        "title": "Health Insurance",
        "description": "Subsidize health insurance cost.",
        "icon": "🩺",
    },
}

PERIOD_KEY_MAP = {
    "Daily": "day",
    "Weekly": "week",
    "Yearly": "year",
}


def _get_value_for_category(reward_table, category: str) -> float:
    matches = reward_table.loc[reward_table["category"] == category, "dollar_value"]
    return float(matches.iloc[0]) if not matches.empty else 0.0


def main() -> None:
    st.set_page_config(page_title="Healthy 365 Rewards Explorer", layout="wide")
    st.title("Healthy 365 Rewards Explorer")
    st.write("Adjust your weekly habits to estimate reward dollar value by period.")

    st.subheader("Inputs")
    input_cols = st.columns(3)
    with input_cols[0]:
        daily_steps = st.number_input(
            "Daily step count",
            min_value=0,
            max_value=50000,
            value=7500,
            step=500,
        )
    with input_cols[1]:
        daily_sleep_hours = st.number_input(
            "Sleep (hours)",
            min_value=0.0,
            max_value=24.0,
            value=7.0,
            step=0.1,
            format="%.1f",
        )
    with input_cols[2]:
        weekly_exercise_minutes = st.number_input(
            "Exercise minutes per week",
            min_value=0,
            max_value=2000,
            value=90,
            step=10,
        )
    has_health_screening = st.checkbox("Did a Health Screening this year", value=False)

    period_label = st.selectbox(
        "Display reward period",
        options=["Daily", "Weekly", "Yearly"],
        index=2,
    )
    period_key = PERIOD_KEY_MAP[period_label]

    inputs = HealthInputs(
        daily_steps=int(daily_steps),
        daily_sleep_hours=float(daily_sleep_hours),
        weekly_exercise_minutes=int(weekly_exercise_minutes),
        has_health_screening=has_health_screening,
    )
    result = build_health_reward_objects(inputs)
    reward_table = result["rewards_by_period"][period_key]

    st.subheader("Rewards")
    cols = st.columns(3)
    ordered_categories = ["activesg", "retail_vouchers", "health_insurance"]

    for col, category in zip(cols, ordered_categories):
        info = CARD_CONFIG[category]
        with col:
            st.subheader(info["title"])
            st.caption(info["description"])
            st.markdown(f"## {info['icon']}")
            value = _get_value_for_category(reward_table, category)
            st.metric(label=f"{period_label} Dollar Value", value=f"${value:,.2f}")


if __name__ == "__main__":
    main()
