from pathlib import Path
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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


def money(v: float) -> str:
    return f"${v:,.0f}"


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def init_state():
    if "salary_working_df" not in st.session_state:
        st.session_state.salary_working_df = load_csv(DATA_DIR / "salary_table.csv")
    if "meeting_working_df" not in st.session_state:
        st.session_state.meeting_working_df = load_csv(DATA_DIR / "meetings.csv")
    if "solution_name" not in st.session_state:
        st.session_state.solution_name = "Requested API"
    if "annual_solution_cost" not in st.session_state:
        st.session_state.annual_solution_cost = 5000.0
    if "requested_date" not in st.session_state:
        st.session_state.requested_date = date(date.today().year - 1, date.today().month, 1)


def months_between(start: date, end: date) -> int:
    return max((end.year - start.year) * 12 + (end.month - start.month), 0)


init_state()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("Navigation")
    view_mode = st.radio("", ["Dashboard", "Calculator & Inputs"], index=0)

    st.markdown("---")
    st.subheader("Solution")

    with st.form("form"):
        solution_name = st.text_input("Solution name", st.session_state.solution_name)
        solution_cost = st.number_input("Annual cost ($)", value=st.session_state.annual_solution_cost)
        requested_date = st.date_input("Date requested", value=st.session_state.requested_date)

        submit = st.form_submit_button("Recalculate")

    if submit:
        st.session_state.solution_name = solution_name
        st.session_state.annual_solution_cost = solution_cost
        st.session_state.requested_date = requested_date

# ---------- DATA ----------
salary_df = pd.DataFrame(st.session_state.salary_working_df)
meetings_df = pd.DataFrame(st.session_state.meeting_working_df)

salary_df = clean_salary_table(salary_df)
roles = salary_df["role"].tolist()

meeting_df = clean_meeting_table(meetings_df, roles)

result_df, metrics = calculate_meeting_costs(salary_df, meeting_df, roles)

total_cost = metrics["total_cost"]
solution_total = st.session_state.annual_solution_cost

comparison = calculate_comparison_metrics(total_cost, solution_total)

months_since = months_between(st.session_state.requested_date, date.today())

# ---------- HEADER ----------
left, right = st.columns([1.2, 1])

with left:
    st.title("MEETING COST CALCULATOR")
    st.caption("Calculate the true cost of delay.")

with right:
    st.markdown(f"""
    <div style="border:1px solid #d0daea;border-radius:12px;padding:16px;background:#f5f8ff;">
        <b>Solution Cost</b><br>
        {st.session_state.solution_name}<br>
        <span style="font-size:28px;font-weight:bold;">{money(solution_total)}</span><br>
        per year
    </div>
    """, unsafe_allow_html=True)

# ---------- MAIN ----------
col1, col2 = st.columns([1, 1.1])

with col1:
    st.subheader("Salary Table")
    st.dataframe(salary_df, use_container_width=True)

    st.subheader("Meetings")
    st.dataframe(meeting_df, use_container_width=True)

with col2:
    st.subheader("Total Cost of Meetings")

    st.markdown(f"""
    <div style="font-size:42px;color:green;font-weight:bold;">
        {money(total_cost)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="border:1px solid #d0daea;border-radius:10px;padding:12px;text-align:center;">
        <div>That's</div>
        <div style="font-size:32px;font-weight:bold;">{comparison['cost_multiple']:.1f}x</div>
        <div>the cost of the solution</div>
    </div>
    """, unsafe_allow_html=True)

    piggy = ASSET_DIR / "piggy_bank_flying_money.png"
    if piggy.exists():
        st.image(str(piggy), use_container_width=True)

    # ---------- CHART ----------
    st.subheader("Cumulative Cost Over Time")

    if "meeting_date" in result_df.columns:
        df = result_df.dropna(subset=["meeting_date"])

        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(df["meeting_date"], df["cumulative_cost"], color="green", marker="o")
        ax.fill_between(df["meeting_date"], df["cumulative_cost"], alpha=0.1)

        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.xticks(rotation=30)
        st.pyplot(fig)

# ---------- BANNER ----------
roi = ((total_cost - solution_total) / solution_total * 100) if solution_total else 0

st.markdown(f"""
<div style="margin-top:20px;padding:14px;border-radius:10px;background:#fff8e1;border:1px solid #e8d98a;">
    💡 <b>Stop the drain.</b> Invest {money(solution_total)} to avoid {money(total_cost)} in wasted meeting cost.
    <span style="float:right;font-weight:bold;">ROI: {roi:,.0f}%</span>
</div>
""", unsafe_allow_html=True)
