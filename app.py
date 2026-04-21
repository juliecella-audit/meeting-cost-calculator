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


def load_uploaded_or_default(uploaded, default_path: Path) -> pd.DataFrame:
    return pd.read_csv(uploaded) if uploaded is not None else load_csv(default_path)


def months_between(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(months, 0)


def init_state() -> None:
    if "salary_working_df" not in st.session_state:
        st.session_state.salary_working_df = load_csv(DATA_DIR / "salary_table.csv")
    if "meeting_working_df" not in st.session_state:
        st.session_state.meeting_working_df = load_csv(DATA_DIR / "meetings.csv")
    if "solution_name" not in st.session_state:
        st.session_state.solution_name = "Requested API"
    if "annual_solution_cost" not in st.session_state:
        st.session_state.annual_solution_cost = 5000.0
    if "one_time_cost" not in st.session_state:
        st.session_state.one_time_cost = 0.0
    if "requested_date" not in st.session_state:
        st.session_state.requested_date = date(date.today().year - 1, date.today().month, 1)
    if "show_prep_cost" not in st.session_state:
        st.session_state.show_prep_cost = True
    if "months_of_meetings" not in st.session_state:
        st.session_state.months_of_meetings = 12
    if "meeting_length" not in st.session_state:
        st.session_state.meeting_length = 1.0
    if "fully_loaded" not in st.session_state:
        st.session_state.fully_loaded = "Yes"


init_state()

st.markdown("""
<style>
.block-container { padding-top: 1.1rem; padding-bottom: 2rem; }
[data-testid="stSidebar"] { background: #f7f9fc; }

h2, h3 { letter-spacing: .02em; }

.solution-bar {
    border: 1.5px solid #d0daea;
    border-radius: 14px;
    padding: 16px 22px;
    background: #f5f8ff;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
}
.solution-bar-label { color: #173f8a; font-size: 0.92rem; font-weight: 700; text-transform: uppercase; letter-spacing:.04em; }
.solution-bar-sub   { color: #3a5798; font-size: 0.88rem; margin-top: 3px; }
.solution-bar-value { color: #1746a2; font-size: 2.6rem; font-weight: 800; line-height: 1; text-align: right; }
.solution-bar-per   { color: #1746a2; font-size: 0.9rem; font-weight: 600; text-align: right; }

.sec-header {
    background: #0e2354;
    color: #ffffff;
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .07em;
    padding: 10px 14px;
    border-radius: 10px 10px 0 0;
    margin-bottom: 0;
}
.sec-body {
    border: 1.5px solid #d0daea;
    border-top: none;
    border-radius: 0 0 10px 10px;
    padding: 12px 14px 14px 14px;
    background: #ffffff;
    margin-bottom: 16px;
}

.cost-hero-panel {
    border: 1.5px solid #d0daea;
    border-radius: 0 0 10px 10px;
    border-top: none;
    background: #ffffff;
    padding: 14px 16px 16px 16px;
    margin-bottom: 16px;
}
.cost-big-number { color: #13823b; font-size: 3rem; font-weight: 800; line-height: 1; margin-bottom: 6px; }
.cost-label      { color: #1c2330; font-size: 1.05rem; font-weight: 700; }
.cost-sub        { color: #5b6470; font-size: 0.9rem; }

.multiplier-box  {
    border: 1.5px solid #d0daea;
    border-radius: 10px;
    padding: 14px 14px;
    background: #f8faff;
    text-align: center;
    margin-bottom: 12px;
}
.mult-that  { color: #5b6470; font-size: 0.9rem; }
.mult-num   { color: #1746a2; font-size: 2.5rem; font-weight: 800; line-height: 1.1; }
.mult-desc  { color: #3a5798; font-size: 0.9rem; }

.api-cost-box {
    border: 1.5px solid #d0daea;
    border-radius: 10px;
    padding: 14px 14px;
    background: #f8faff;
    text-align: center;
}
.api-cost-label  { color: #5b6470; font-size: 0.86rem; margin-bottom: 4px; }
.api-cost-value  { color: #1746a2; font-size: 1.7rem; font-weight: 800; }

.chart-ann {
    border: 1.5px solid #d0daea;
    border-radius: 10px;
    padding: 16px 14px;
    background: #f8faff;
    text-align: center;
}
.chart-ann-label { color: #5b6470; font-size: 0.9rem; }
.chart-ann-value { color: #13823b; font-size: 2.2rem; font-weight: 800; }

.banner {
    background: #fffbec;
    border: 1.5px solid #e8d98a;
    border-radius: 12px;
    padding: 16px 22px;
    margin: 8px 0 18px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
}
.banner-left  { color: #4f4011; font-size: 1rem; }
.banner-left strong { font-size: 1.08rem; }
.banner-roi   { color: #b88000; font-size: 1rem; font-weight: 700; white-space: nowrap; }
.banner-roi span { font-size: 1.6rem; }

.small-helper { color: #6a7384; font-size: 0.88rem; }
.recalc-note { color: #6a7384; font-size: 0.82rem; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.header("Navigation")
    view_mode = st.radio(
        "View",
        ["Dashboard", "Calculator & Inputs"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.subheader("Solution")
    with st.form("solution_form", clear_on_submit=False):
        solution_name_input = st.text_input("Solution name", value=st.session_state.solution_name)
        annual_solution_cost_input = st.number_input(
            "Annual cost ($)",
            min_value=0.0,
            value=float(st.session_state.annual_solution_cost),
            step=500.0,
        )
        one_time_cost_input = st.number_input(
            "One-time cost ($)",
            min_value=0.0,
            value=float(st.session_state.one_time_cost),
            step=500.0,
        )
        requested_date_input = st.date_input(
            "Date requested",
            value=st.session_state.requested_date,
        )
        show_prep_cost_input = st.toggle(
            "Include prep hours",
            value=bool(st.session_state.show_prep_cost),
        )
        months_of_meetings_input = st.number_input(
            "Months of Meetings",
            min_value=1,
            value=int(st.session_state.months_of_meetings),
            step=1,
        )
        meeting_length_input = st.number_input(
            "Meeting Length (hours)",
            min_value=0.25,
            value=float(st.session_state.meeting_length),
            step=0.25,
        )
        fully_loaded_input = st.selectbox(
            "Fully Loaded Cost?",
            ["Yes", "No"],
            index=0 if st.session_state.fully_loaded == "Yes" else 1,
        )
        recalc = st.form_submit_button("Recalculate Cost", use_container_width=True)

    st.markdown('<div class="recalc-note">Update the fields above, then click Recalculate Cost.</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Upload replacement CSVs")
    salary_upload = st.file_uploader("Salary table CSV", type=["csv"])
    meeting_upload = st.file_uploader("Meeting log CSV", type=["csv"])

if recalc:
    st.session_state.solution_name = solution_name_input
    st.session_state.annual_solution_cost = annual_solution_cost_input
    st.session_state.one_time_cost = one_time_cost_input
    st.session_state.requested_date = requested_date_input
    st.session_state.show_prep_cost = show_prep_cost_input
    st.session_state.months_of_meetings = months_of_meetings_input
    st.session_state.meeting_length = meeting_length_input
    st.session_state.fully_loaded = fully_loaded_input

if salary_upload is not None:
    st.session_state.salary_working_df = pd.read_csv(salary_upload)

if meeting_upload is not None:
    st.session_state.meeting_working_df = pd.read_csv(meeting_upload)

salary_df_raw = pd.DataFrame(st.session_state.salary_working_df)
meetings_df_raw = pd.DataFrame(st.session_state.meeting_working_df)

solution_name = st.session_state.solution_name
annual_solution_cost = float(st.session_state.annual_solution_cost)
one_time_cost = float(st.session_state.one_time_cost)
requested_date = st.session_state.requested_date
show_prep_cost = bool(st.session_state.show_prep_cost)
months_of_meetings = int(st.session_state.months_of_meetings)
meeting_length = float(st.session_state.meeting_length)
fully_loaded = st.session_state.fully_loaded

solution_total = annual_solution_cost + one_time_cost


title_col, sol_col = st.columns([1.1, 1], gap="large")

with title_col:
    st.markdown("## MEETING COST CALCULATOR")
    st.caption("Calculate the true cost of meetings while waiting for a solution.  \nSee the impact of time, people, and delay.")

with sol_col:
    st.markdown(f"""
    <div class="solution-bar">
        <div>
            <div class="solution-bar-label">Solution Cost <span style="font-weight:400;color:#3a5798;">(Physical Cost)</span></div>
            <div class="solution-bar-sub">Annual Cost of {solution_name}</div>
        </div>
        <div>
            <div class="solution-bar-value">{money(solution_total)}</div>
            <div class="solution-bar-per">per year</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

left_col, right_col = st.columns([1, 1.05], gap="large")

with left_col:
    st.markdown('<div class="sec-header">1. &nbsp;Average Salary Table <span style="font-weight:400;opacity:.7;">(Loaded)</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-body">', unsafe_allow_html=True)
    salary_df = st.data_editor(
        salary_df_raw,
        use_container_width=True,
        num_rows="dynamic",
        key="salary_editor",
        hide_index=True,
    )
    st.session_state.salary_working_df = salary_df
    st.caption("*Loaded hourly rate includes benefits and overhead (2,080 hours per year)")
    st.markdown('</div>', unsafe_allow_html=True)

    salary_calc_df = clean_salary_table(salary_df.copy())
    roles = salary_calc_df["role"].astype(str).tolist()

    st.markdown('<div class="sec-header">2. &nbsp;Meetings Input</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-body">', unsafe_allow_html=True)
    meetings_df = st.data_editor(
        meetings_df_raw,
        use_container_width=True,
        num_rows="dynamic",
        key="meeting_editor",
        hide_index=True,
    )
    st.session_state.meeting_working_df = meetings_df
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-header">3. &nbsp;Assumptions</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-body">', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        st.metric("Meeting Length (hours)", f"{meeting_length:.2f}")
    with a2:
        st.metric("Months of Meetings", months_of_meetings)
    with a3:
        st.metric("Fully Loaded Cost?", fully_loaded)
    st.info("This calculator shows the internal cost of meetings and delays.  \n**The true cost of delay is more than just money.**")
    st.markdown('</div>', unsafe_allow_html=True)

with right_col:
    meeting_calc_df = clean_meeting_table(meetings_df.copy(), roles)
    result_df, metrics = calculate_meeting_costs(salary_calc_df, meeting_calc_df, roles)
    total_cost = metrics["total_cost"] if show_prep_cost else metrics["total_meeting_cost"]
    comparison = calculate_comparison_metrics(total_cost, solution_total)
    role_summary_df = calculate_role_summary(result_df, roles)
    months_since_request = months_between(requested_date, date.today())
    roi_pct = ((total_cost - solution_total) / solution_total * 100) if solution_total > 0 else 0.0

    st.markdown('<div class="sec-header">Total Cost of Meetings</div>', unsafe_allow_html=True)
    st.markdown('<div class="cost-hero-panel">', unsafe_allow_html=True)

    inner_left, inner_right = st.columns([1.35, 0.8], gap="medium")

    with inner_left:
        st.markdown(f"""
        <div class="cost-big-number">{money(total_cost)}</div>
        <div class="cost-label">Total Spent in Meetings</div>
        <div class="cost-sub">(Over {months_since_request or months_of_meetings} Months)</div>
        """, unsafe_allow_html=True)

        piggy_path = ASSET_DIR / "piggy_bank_flying_money.png"
        if piggy_path.exists():
            st.image(str(piggy_path), use_container_width=True)
        else:
            st.markdown(
                "<div style='font-size:6rem;text-align:center;padding:24px 0;'>🐷</div>"
                "<div class='small-helper' style='text-align:center;'>Add assets/piggy_bank_flying_money.png to show the piggy bank artwork.</div>",
                unsafe_allow_html=True,
            )

    with inner_right:
        st.markdown(f"""
        <div class="multiplier-box">
            <div class="mult-that">That's</div>
            <div class="mult-num">{comparison['cost_multiple']:.1f}x</div>
            <div class="mult-desc">the cost of the<br>{solution_name} per year!</div>
        </div>
        <div class="api-cost-box">
            <div class="api-cost-label">API Annual Cost</div>
            <div class="api-cost-value">{money(solution_total)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-header">Cumulative Cost Over Time</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-body">', unsafe_allow_html=True)

    chart_col, ann_col = st.columns([1.6, 0.6], gap="medium")

    with chart_col:
        if not result_df.empty and "meeting_date" in result_df.columns:
            plot_df = result_df.dropna(subset=["meeting_date"]).copy()
            fig, ax = plt.subplots(figsize=(6, 3.2))
            ax.plot(
                plot_df["meeting_date"],
                plot_df["cumulative_cost"],
                color="#13823b",
                marker="o",
                markersize=5,
                linewidth=2,
            )
            ax.fill_between(
                plot_df["meeting_date"],
                plot_df["cumulative_cost"],
                alpha=0.08,
                color="#13823b",
            )
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
            ax.tick_params(axis="both", labelsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Add meeting dates to display the trend.")

    with ann_col:
        months_label = months_since_request or months_of_meetings
        st.markdown(f"""
        <div class="chart-ann" style="margin-top:30px;">
            <div class="chart-ann-label">After {months_label} months,<br>you've spent</div>
            <div class="chart-ann-value">{money(total_cost)}</div>
            <div class="chart-ann-label">in meetings.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="banner">
    <div class="banner-left">
        💡 &nbsp;<strong>Stop the drain. Approve the solution.</strong>
        &nbsp; Invest {money(solution_total)} in the {solution_name} to save {money(total_cost)} in people costs.
    </div>
    <div class="banner-roi">Return on Investment: &nbsp;<span>{roi_pct:,.0f}%</span></div>
</div>
""", unsafe_allow_html=True)

if view_mode == "Calculator & Inputs":
    st.markdown("---")
    st.subheader("Calculator & Inputs")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Solution cost", money(solution_total))
    m2.metric("Meeting labor cost", money(total_cost))
    m3.metric("Cost multiple", f"{comparison['cost_multiple']:.1f}x" if solution_total > 0 else "n/a")
    m4.metric("Months since request", months_since_request)

    cl, cr = st.columns(2, gap="large")
    with cl:
        st.subheader("Loaded salary rates")
        ds = salary_calc_df.copy()
        for c in ["annual_salary", "loaded_annual_cost", "loaded_hourly_rate"]:
            if c in ds.columns:
                ds[c] = ds[c].map(lambda x: round(float(x), 2))
        st.dataframe(ds, use_container_width=True, hide_index=True)

    with cr:
        st.subheader("Calculated meeting details")
        detail_cols = [
            "meeting_name", "meeting_date", "duration_hours", "number_of_meetings",
            "total_people", "meeting_cost", "prep_cost", "total_row_cost", "cumulative_cost"
        ]
        existing = [c for c in detail_cols if c in result_df.columns]
        st.dataframe(result_df[existing] if existing else result_df, use_container_width=True, hide_index=True)

    if solution_total > 0:
        st.info(
            f"Your organisation has spent {money(total_cost)} on meetings related to {solution_name} — "
            f"{comparison['cost_multiple']:.1f}× the solution cost."
        )

    if not role_summary_df.empty:
        st.subheader("Cost by role")
        fig3, ax3 = plt.subplots(figsize=(9, 3.5))
        ax3.bar(role_summary_df["role"], role_summary_df["cost"], color="#1746a2")
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        plt.xticks(rotation=35, ha="right", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig3)

st.markdown("---")
dl1, dl2 = st.columns(2)
with dl1:
    st.download_button(
        "⬇ Download salary table CSV",
        data=salary_calc_df.to_csv(index=False).encode("utf-8"),
        file_name="salary_table_updated.csv",
        mime="text/csv",
    )
with dl2:
    st.download_button(
        "⬇ Download meeting results CSV",
        data=result_df.to_csv(index=False).encode("utf-8"),
        file_name="meeting_results.csv",
        mime="text/csv",
    )
