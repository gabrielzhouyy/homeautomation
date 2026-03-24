#!/usr/bin/env python3
"""
Data-only Healthy 365 style points and rewards projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import pandas as pd


@dataclass(frozen=True)
class HealthInputs:
	"""Average behavior inputs used for point projections."""

	daily_steps: int
	daily_sleep_hours: float
	weekly_exercise_minutes: int
	has_health_screening: bool
	weekly_food_purchases: int = 0
	weekly_grocery_purchases: int = 0


# Threshold tables are sorted from highest threshold to lowest threshold.
SLEEP_RULES = pd.DataFrame(
	{
		"threshold": [7.0, 6.5, 6.0],
		"points": [15, 10, 5],
	}
)

STEPS_RULES = pd.DataFrame(
	{
		"threshold": [15000, 10000, 5000],
		"points": [15, 10, 5],
	}
)

EXERCISE_RULES = pd.DataFrame(
	{
		"threshold": [150, 120, 90, 60, 30],
		"points": [100, 80, 60, 40, 20],
	}
)

FOOD_PURCHASES_RULES = {
	"points_per_item": 10,
	"max_items_per_week": 15,
}

GROCERY_PURCHASES_RULES = {
	"points_per_item": 5,
	"max_items_per_week": 15,
}

REWARD_RULES = pd.DataFrame(
	{
		"category": [
			"activesg",
			"retail_vouchers",
			"health_insurance",
		],
		"points_per_unit": [1, 1, 1],
		"unit_value": [0.02, 0.00667, 0.01333],
	}
)

YEARLY_SCREENING_POINTS = 3000
WEEKS_PER_YEAR = 53
DAYS_PER_WEEK = 7


def _points_from_threshold(value: float, rule_table: pd.DataFrame) -> int:
	"""Return points for the highest threshold satisfied by value."""
	eligible = rule_table.loc[value >= rule_table["threshold"], "points"]
	return int(eligible.iloc[0]) if not eligible.empty else 0


def _points_from_purchases(items_purchased: int, rule_dict: Dict[str, int]) -> int:
	"""Calculate points from purchases with a per-item rate and weekly cap."""
	capped_items = min(items_purchased, rule_dict["max_items_per_week"])
	return capped_items * rule_dict["points_per_item"]


def _build_reward_table(total_points: float) -> pd.DataFrame:
	"""Build reward outcomes for a single point total."""
	table = REWARD_RULES.copy()
	table["total_points"] = float(total_points)
	redemption_count = (table["total_points"] // table["points_per_unit"]).astype(int)
	table["dollar_value"] = redemption_count * table["unit_value"]
	return table[
		[
			"category",
			"total_points",
			"dollar_value",
		]
	]


def aggregate_points_weekly(inputs: HealthInputs) -> Dict[str, float]:
	"""Aggregate points at weekly grain, then derive daily and yearly values."""
	daily_habit_points = _points_from_threshold(inputs.daily_steps, STEPS_RULES) + _points_from_threshold(
		inputs.daily_sleep_hours, SLEEP_RULES
	)
	weekly_habit_points = daily_habit_points * DAYS_PER_WEEK
	weekly_exercise_points = _points_from_threshold(inputs.weekly_exercise_minutes, EXERCISE_RULES)
	weekly_food_points = _points_from_purchases(inputs.weekly_food_purchases, FOOD_PURCHASES_RULES)
	weekly_grocery_points = _points_from_purchases(inputs.weekly_grocery_purchases, GROCERY_PURCHASES_RULES)
	weekly_screening_attribution = (
		YEARLY_SCREENING_POINTS / WEEKS_PER_YEAR if inputs.has_health_screening else 0.0
	)

	weekly_points = weekly_habit_points + weekly_exercise_points + weekly_food_points + weekly_grocery_points + weekly_screening_attribution
	daily_points = weekly_points / DAYS_PER_WEEK
	yearly_points = weekly_points * WEEKS_PER_YEAR

	return {
		"points_per_day": float(round(daily_points, 2)),
		"points_per_week": float(round(weekly_points, 2)),
		"points_per_year": float(round(yearly_points, 2)),
	}


def build_rewards_from_points(points_summary: Dict[str, float]) -> Dict[str, Any]:
	"""Build reward tables from already-aggregated period points."""
	rewards_by_period = {
		"day": _build_reward_table(points_summary["points_per_day"]),
		"week": _build_reward_table(points_summary["points_per_week"]),
		"year": _build_reward_table(points_summary["points_per_year"]),
	}

	rewards_all_periods = pd.concat(
		[
			rewards_by_period["day"].assign(period="day"),
			rewards_by_period["week"].assign(period="week"),
			rewards_by_period["year"].assign(period="year"),
		],
		ignore_index=True,
	)

	return {
		"rewards_by_period": rewards_by_period,
		"rewards_all_periods": rewards_all_periods,
	}


def build_health_reward_objects(inputs: HealthInputs) -> Dict[str, Any]:
	"""
	Return the requested objects:
	1) Number of points per day (average)
	2) Number of points per week
	3) Number of points per year
	4) Rewards by category for (1), (2), and (3)
	"""
	points_summary = aggregate_points_weekly(inputs)
	rewards = build_rewards_from_points(points_summary)
	return {**points_summary, **rewards}


if __name__ == "__main__":
	sample_inputs = HealthInputs(
		daily_steps=6000,
		daily_sleep_hours=8,
		weekly_exercise_minutes=200,
		has_health_screening=True,
	)
	output = build_health_reward_objects(sample_inputs)

	print("Points Summary")
	print({k: output[k] for k in ("points_per_day", "points_per_week", "points_per_year")})
	print("\nRewards (all periods)")
	print(output["rewards_all_periods"].to_string(index=False))