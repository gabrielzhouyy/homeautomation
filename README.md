# HPB Tracking and Rewards

This repository also includes a data-only health points and rewards module:
- `health_rewards_data.py`
- Uses pandas rule tables (no UI widgets)
- Returns plain Python objects and DataFrames for analysis

```

## Health Points Data Module

`health_rewards_data.py` provides a clean, data-only API for points and rewards projection.

### What It Returns

Calling `build_health_reward_objects(...)` returns these objects:
1. `points_per_day` (average daily points)
2. `points_per_week`
3. `points_per_year`
4. Rewards for each category for day/week/year:
   - `rewards_by_period` (dict of DataFrames for `day`, `week`, `year`)
   - `rewards_all_periods` (single combined DataFrame)

### Usage

```python
from health_rewards_data import HealthInputs, build_health_reward_objects

inputs = HealthInputs(
   daily_steps=7500,
   daily_sleep_hours=7.0,
   weekly_exercise_minutes=90,
   has_health_screening=False,
)

result = build_health_reward_objects(inputs)

print(result["points_per_day"])
print(result["points_per_week"])
print(result["points_per_year"])

print(result["rewards_by_period"]["year"])
print(result["rewards_all_periods"])
```

### Run Module Directly

```bash
source venv/bin/activate
python3 health_rewards_data.py
```
