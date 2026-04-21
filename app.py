
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from utils.calculations import (
    calculate_comparison_metrics,
    calculate_meeting_costs,
    calculate_role_summary,
    clean_meeting_table,
    clean_salary_table,
)


st.set_page_config(page_title="Meeting Cost Calculator", layout="wide")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSET_DIR = BASE_DIR / "assets"


def money(value: float) -> str:
    return f"${value:,.0f}"


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


st.title("Meeting Cost Calculator")
st.caption("Quantify the labor cost of repeated meetings while waiting for a lower-cost solution.")

with st.sidebar:
    st.header("Solution assumptions")
    solution_name = st.text_input("Solution name", value="Requested API")
    annual_solution_cost = st.number_input("Annual solution cost", min_value=0.0, value=5000.0, step=500.0)
    one_time_cost = st.number_input("One-time implementation cost", min_value=0.0, value=0.0, step=500.0)
    show_prep_cost = st.toggle("Include prep hours in total cost", value=True)
    st.markdown("---")
    st.write("Tip: edit the salary and meeting tables directly in the app.")

salary_df = load_csv(DATA_DIR / "salary_table.csv")
meetings_df = load_csv(DATA_DIR / "meetings.csv")

st.subheader("1. Salary table")
edited_salary_df = st.data_editor(
    salary_df,
    use_container_width=True,
    num_rows="dynamic",
    key="salary_editor",
)

salary_calc_df = clean_salary_table(edited_salary_df)
roles = salary_calc_df["role"].astype(str).tolist()

st.subheader("2. Meeting log")
edited_meetings_df = st.data_editor(
    meetings_df,
    use_container_width=True,
    num_rows="dynamic",
    key="meeting_editor",
)

meeting_calc_df = clean_meeting_table(edited_meetings_df, roles)
result_df, metrics = calculate_meeting_costs(salary_calc_df, meeting_calc_df, roles)

total_cost = metrics["total_cost"] if show_prep_cost else metrics["total_meeting_cost"]
solution_total = annual_solution_cost + one_time_cost
comparison = calculate_comparison_metrics(total_cost, solution_total)
role_summary_df = calculate_role_summary(result_df, roles)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Solution cost", money(solution_total))
col2.metric("Meeting labor cost", money(total_cost))
col3.metric("Cost multiple", f"{comparison['cost_multiple']:.1f}x" if solution_total > 0 else "n/a")
col4.metric("Meetings logged", f"{metrics['total_meetings']:.0f}")

left, right = st.columns([1.05, 1.3], gap="large")

with left:
    st.subheader("Loaded salary rates")
    display_salary = salary_calc_df.copy()
    for col in ["annual_salary", "loaded_annual_cost", "loaded_hourly_rate"]:
        display_salary[col] = display_salary[col].map(lambda x: round(float(x), 2))
    st.dataframe(display_salary, use_container_width=True, hide_index=True)

    st.subheader("Narrative")
    if solution_total > 0:
        st.info(
            f"Based on the values entered, your organization has spent {money(total_cost)} on meetings "
            f"related to {solution_name}. That is {comparison['cost_multiple']:.1f} times the entered cost "
            f"of the solution."
        )
    else:
        st.info(
            f"Based on the values entered, your organization has spent {money(total_cost)} on meetings "
            f"related to {solution_name}."
        )

    st.subheader("Calculated meeting details")
    display_cols = [
        "meeting_name",
        "meeting_date",
        "duration_hours",
        "number_of_meetings",
        "total_people",
        "meeting_cost",
        "prep_cost",
        "total_row_cost",
        "cumulative_cost",
    ]
    existing_cols = [c for c in display_cols if c in result_df.columns]
    show_df = result_df[existing_cols].copy() if not result_df.empty else pd.DataFrame(columns=existing_cols)
    st.dataframe(show_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("Dashboard")
    hero_a, hero_b = st.columns([1.15, 1])

    with hero_a:
        piggy_path = ASSET_DIR / "piggy_bank_mockup.png"
        if piggy_path.exists():
            st.image(str(piggy_path), use_container_width=True)
        else:
            st.warning("Piggy bank image not found.")

    with hero_b:
        st.metric("Total spent in meetings", money(total_cost))
        st.metric("Annual solution cost", money(solution_total))
        st.metric("Difference", money(comparison["net_over_solution"]))
        st.write("")
        if solution_total > 0 and total_cost > solution_total:
            st.success("The cost of delay is now higher than the cost of the solution.")
        else:
            st.warning("The meeting cost has not yet exceeded the solution cost.")

    st.subheader("Cumulative cost over time")
    if not result_df.empty and "meeting_date" in result_df.columns:
        plot_df = result_df.dropna(subset=["meeting_date"]).copy()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(plot_df["meeting_date"], plot_df["cumulative_cost"], marker="o")
        ax.set_xlabel("Meeting date")
        ax.set_ylabel("Cumulative cost ($)")
        ax.ticklabel_format(style="plain", axis="y")
        st.pyplot(fig)
    else:
        st.info("Add meeting dates to display the cumulative trend chart.")

    st.subheader("Cost by role")
    if not role_summary_df.empty:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(role_summary_df["role"], role_summary_df["cost"])
        ax2.set_xlabel("Role")
        ax2.set_ylabel("Cost ($)")
        ax2.ticklabel_format(style="plain", axis="y")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig2)
    else:
        st.info("Add meetings and role counts to show role-based cost.")

st.subheader("Download current working tables")
dl1, dl2 = st.columns(2)
with dl1:
    st.download_button(
        "Download salary table CSV",
        data=salary_calc_df.to_csv(index=False).encode("utf-8"),
        file_name="salary_table_updated.csv",
        mime="text/csv",
    )
with dl2:
    st.download_button(
        "Download meeting results CSV",
        data=result_df.to_csv(index=False).encode("utf-8"),
        file_name="meeting_results.csv",
        mime="text/csv",
    )
