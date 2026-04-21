
import pandas as pd


HOURS_PER_YEAR = 2080


def clean_salary_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = ["annual_salary", "load_pct"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    out["loaded_annual_cost"] = out["annual_salary"] * (1 + out["load_pct"])
    out["loaded_hourly_rate"] = out["loaded_annual_cost"] / HOURS_PER_YEAR
    return out


def clean_meeting_table(df: pd.DataFrame, roles: list[str]) -> pd.DataFrame:
    out = df.copy()

    for col in ["duration_hours", "number_of_meetings", "prep_hours_per_person"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    if "meeting_date" in out.columns:
        out["meeting_date"] = pd.to_datetime(out["meeting_date"], errors="coerce")

    for role in roles:
        if role not in out.columns:
            out[role] = 0
        out[role] = pd.to_numeric(out[role], errors="coerce").fillna(0).astype(int)

    return out


def calculate_meeting_costs(
    salary_df: pd.DataFrame,
    meetings_df: pd.DataFrame,
    roles: list[str],
) -> tuple[pd.DataFrame, dict]:
    rate_map = salary_df.set_index("role")["loaded_hourly_rate"].to_dict()

    rows = []
    for _, row in meetings_df.iterrows():
        row_result = row.to_dict()
        total_people = 0
        attendee_cost = 0.0
        prep_cost = 0.0

        for role in roles:
            count = int(row.get(role, 0) or 0)
            rate = float(rate_map.get(role, 0.0))
            duration = float(row.get("duration_hours", 0.0) or 0.0)
            num_meetings = float(row.get("number_of_meetings", 0.0) or 0.0)
            prep_hours = float(row.get("prep_hours_per_person", 0.0) or 0.0)

            role_meeting_cost = count * rate * duration * num_meetings
            role_prep_cost = count * rate * prep_hours * num_meetings

            row_result[f"{role}_cost"] = role_meeting_cost
            attendee_cost += role_meeting_cost
            prep_cost += role_prep_cost
            total_people += count

        row_result["total_people"] = total_people
        row_result["meeting_cost"] = attendee_cost
        row_result["prep_cost"] = prep_cost
        row_result["total_row_cost"] = attendee_cost + prep_cost
        rows.append(row_result)

    result_df = pd.DataFrame(rows)
    expected_cols = [
        "meeting_name",
        "meeting_date",
        "duration_hours",
        "number_of_meetings",
        "prep_hours_per_person",
        "total_people",
        "meeting_cost",
        "prep_cost",
        "total_row_cost",
        "cumulative_cost",
    ]
    for col in expected_cols:
        if col not in result_df.columns:
            if col == "meeting_name":
                result_df[col] = ""
            elif col == "meeting_date":
                result_df[col] = pd.NaT
            else:
                result_df[col] = 0.0

    if "meeting_date" in result_df.columns:
        result_df = result_df.sort_values("meeting_date", kind="stable")

    result_df["cumulative_cost"] = result_df["total_row_cost"].cumsum()

    total_meeting_cost = float(result_df["meeting_cost"].sum()) if not result_df.empty else 0.0
    total_prep_cost = float(result_df["prep_cost"].sum()) if not result_df.empty else 0.0
    total_cost = float(result_df["total_row_cost"].sum()) if not result_df.empty else 0.0
    total_meetings = float(result_df["number_of_meetings"].sum()) if "number_of_meetings" in result_df.columns and not result_df.empty else 0.0
    total_people = int(result_df["total_people"].sum()) if not result_df.empty else 0
    total_hours = float((result_df["duration_hours"] * result_df["number_of_meetings"]).sum()) if not result_df.empty else 0.0

    metrics = {
        "total_meeting_cost": total_meeting_cost,
        "total_prep_cost": total_prep_cost,
        "total_cost": total_cost,
        "total_meetings": total_meetings,
        "total_people": total_people,
        "total_hours": total_hours,
    }

    return result_df, metrics


def calculate_role_summary(result_df: pd.DataFrame, roles: list[str]) -> pd.DataFrame:
    rows = []
    for role in roles:
        col = f"{role}_cost"
        if col in result_df.columns:
            rows.append({"role": role, "cost": float(result_df[col].sum())})
    return pd.DataFrame(rows).sort_values("cost", ascending=False, kind="stable")


def calculate_comparison_metrics(total_cost: float, solution_cost: float) -> dict:
    if solution_cost and solution_cost > 0:
        cost_multiple = total_cost / solution_cost
        net_over_solution = total_cost - solution_cost
    else:
        cost_multiple = 0.0
        net_over_solution = total_cost

    return {
        "cost_multiple": cost_multiple,
        "net_over_solution": net_over_solution,
    }
