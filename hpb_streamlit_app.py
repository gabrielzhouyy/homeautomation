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
    st.title("Singapore Pays you to Sleep")
    st.markdown(
        "Adjust your weekly habits to estimate reward dollar value by period. "
        "[Get a free fitness tracker here.](https://www.healthhub.sg/programmes/healthyliving/fitnesstracker/features)"
    )

    st.subheader("Inputs")
    input_cols = st.columns(3)
    with input_cols[0]:
        daily_sleep_hours = st.number_input(
            "Sleep (hours)",
            min_value=0.0,
            max_value=24.0,
            value=7.0,
            step=0.1,
            format="%.1f",
        )
    with input_cols[1]:
        weekly_exercise_minutes = st.number_input(
            "Exercise minutes per week",
            min_value=0,
            max_value=2000,
            value=90,
            step=10,
        )
    with input_cols[2]:
        daily_steps = st.number_input(
            "Daily step count",
            min_value=0,
            max_value=50000,
            value=7500,
            step=500,
        )
    
    purchase_cols = st.columns(3)
    with purchase_cols[0]:
        weekly_food_purchases = st.number_input(
            "Weekly Healthapp Food purchases",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
        )
    with purchase_cols[1]:
        weekly_grocery_purchases = st.number_input(
            "Weekly Healthapp Grocery purchases",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
        )
    
    has_health_screening = st.checkbox("Did a Health Screening this year", value=False)

    st.subheader("Choose your Reward")
    period_cols = st.columns([1, 4])
    with period_cols[0]:
        period_label = st.selectbox(
            "Reward Period",
            options=["Daily", "Weekly", "Yearly"],
            index=2,
        )

    period_key = PERIOD_KEY_MAP[period_label]

    inputs = HealthInputs(
        daily_steps=int(daily_steps),
        daily_sleep_hours=float(daily_sleep_hours),
        weekly_exercise_minutes=int(weekly_exercise_minutes),
        has_health_screening=has_health_screening,
        weekly_food_purchases=int(weekly_food_purchases),
        weekly_grocery_purchases=int(weekly_grocery_purchases),
    )
    result = build_health_reward_objects(inputs)
    reward_table = result["rewards_by_period"][period_key]

    cols = st.columns(3)
    ordered_categories = ["activesg", "retail_vouchers", "health_insurance"]

    for col, category in zip(cols, ordered_categories):
        info = CARD_CONFIG[category]
        with col:
            st.markdown(f"### **{info['title']}**")
            st.markdown(f"**{info['description']}**")
            st.markdown(
                f"<div style='text-align:center; font-size:4.5rem; line-height:1.2;'>{info['icon']}</div>",
                unsafe_allow_html=True,
            )
            value = _get_value_for_category(reward_table, category)
            st.metric(label=f"{period_label} Dollar Value", value=f"${value:,.2f}")

    st.divider()

    st.subheader("How It Works")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 🛌 Sleep")
        st.markdown(
            "Track your sleep with a compatible device to earn points for consistent 7+ hours of rest."
        )
    with col2:
        st.markdown("#### 🚶 Move")
        st.markdown(
            "Sync your fitness tracker or phone. Earn points for hitting step milestones "
            "(e.g., 5,000 to 10,000 steps) and for **MVPA**—getting your heart rate up for at least 10 minutes."
        )
    with col3:
        st.markdown("#### 🍽️ Eat")
        st.markdown(
            "Buy a meal or drink with the **Healthier Choice** symbol (lower sugar, whole grains, etc.). "
            "The merchant gives you a QR code. Scan it with the app to get instant points, or purchase from the in-app marketplace to earn points for healthy groceries."
        )

    st.divider()

    st.subheader("Points Calculation")
    st.caption("Quick reference for Healthy 365 points rules.")
    st.table(
        [
            {"Category": "Steps", "Range": "5,000 - 9,999 steps", "Points": "5", "Frequency": "Daily"},
            {"Category": "Steps", "Range": "10,000 - 14,999 steps", "Points": "10", "Frequency": "Daily"},
            {"Category": "Steps", "Range": "15,000+ steps", "Points": "15", "Frequency": "Daily (Max)"},
            {"Category": "Sleep", "Range": "6.0 - 6.4 hours", "Points": "5", "Frequency": "Daily"},
            {"Category": "Sleep", "Range": "6.5 - 6.9 hours", "Points": "10", "Frequency": "Daily"},
            {"Category": "Sleep", "Range": "7.0+ hours", "Points": "15", "Frequency": "Daily (Max)"},
            {
                "Category": "Exercise (Moderate to Vigorous)",
                "Range": "30 - 59 minutes",
                "Points": "20",
                "Frequency": "Weekly",
            },
            {
                "Category": "Exercise (Moderate to Vigorous)",
                "Range": "60 - 89 minutes",
                "Points": "40",
                "Frequency": "Weekly",
            },
            {
                "Category": "Exercise (Moderate to Vigorous)",
                "Range": "90 - 119 minutes",
                "Points": "60",
                "Frequency": "Weekly",
            },
            {
                "Category": "Exercise (Moderate to Vigorous)",
                "Range": "120 - 149 minutes",
                "Points": "80",
                "Frequency": "Weekly",
            },
            {
                "Category": "Exercise (Moderate to Vigorous)",
                "Range": "150+ minutes",
                "Points": "100",
                "Frequency": "Weekly (Max)",
            },
            {"Category": "Healthapp Food Purchases", "Range": "1 - 15 items", "Points": "10 per item", "Frequency": "Weekly"},
            {"Category": "Healthapp Grocery Purchases", "Range": "1 - 15 items", "Points": "5 per item", "Frequency": "Weekly"},
            {"Category": "Screening", "Range": "Completed this year", "Points": "3000", "Frequency": "Yearly"},
        ]
    )
    st.caption("Default conversion reference: 150 points = $1, 2x for insurance, 3x for fitness rewards")


if __name__ == "__main__":
    main()
