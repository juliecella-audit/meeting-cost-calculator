
from pathlib import Path
from datetime import date

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


def load_uploaded_or_default(uploaded_file, default_path: Path) -> pd.DataFrame:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file)
    return load_csv(default_path)


def months_between(start_date: date, end_date: date) -> int:
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day < start_date.day:
        months -= 1
    return max(months, 0)


def animated_currency_card(label: str, value: float, height: int = 160):
    value_int = int(round(value))
    html = f"""
    <div class="hero-card" style="min-height:{height}px;">
        <div class="hero-label">{label}</div>
        <div class="hero-value" id="animated-total">$0</div>
    </div>
    <script>
    const endValue = {value_int};
    const duration = 1800;
    const startTime = performance.now();

    function formatCurrency(num) {{
        return '$' + Math.round(num).toLocaleString();
    }}

    function animateCount(timestamp) {{
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = endValue * eased;
        const el = window.parent.document.getElementById("animated-total") || document.getElementById("animated-total");
        if (el) {{
            el.textContent = formatCurrency(current);
        }}
        if (progress < 1) {{
            requestAnimationFrame(animateCount);
        }}
    }}
    requestAnimationFrame(animateCount);
    </script>
    """
    st.components.v1.html(html, height=height)


st.markdown("""
<style>
.block-container {
    padding-top: 1.6rem;
    padding-bottom: 2rem;
}
.hero-card {
    border: 1px solid #d8e2f0;
    border-radius: 16px;
    padding: 20px 24px;
    background: #ffffff;
    box-shadow: 0 3px 12px rgba(0,0,0,0.05);
}
.hero-label {
    color: #173f8a;
    font-size: 0.95rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: 10px;
}
.hero-value {
    color: #13823b;
    font-size: 3rem;
    font-weight: 800;
    line-height: 1.05;
}
.kpi-card {
    border: 1px solid #e3e8ef;
    border-radius: 14px;
    padding: 14px 16px;
    background: #ffffff;
    min-height: 108px;
}
.kpi-title {
    color: #5b6470;
    font-size: 0.9rem;
    margin-bottom: 6px;
}
.kpi-number {
    color: #1c2330;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
}
.kpi-support {
    color: #5b6470;
    font-size: 0.9rem;
    margin-top: 4px;
}
.banner-box {
    border: 1px solid #e7d9a7;
    background: #fff9e7;
    border-radius: 16px;
    padding: 18px 22px;
    margin-top: 10px;
    margin-bottom: 12px;
}
.banner-title {
    color: #7d5a00;
    font-size: 1.5rem;
    font-weight: 800;
    margin-bottom: 4px;
}
.banner-text {
    color: #4f4f4f;
    font-size: 1.05rem;
}
.section-card {
    border: 1px solid #e3e8ef;
    border-radius: 16px;
    padding: 14px 16px;
    background: #ffffff;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("Meeting Cost Calculator")
st.caption("Calculate the true cost of meetings while waiting for a solution.")

with st.sidebar:
    st.header("Solution assumptions")
    solution_name = st.text_input("Solution name", value="Requested API")
    annual_solution_cost = st.number_input("Annual solution cost", min_value=0.0, value=5000.0, step=500.0)
    one_time_cost = st.number_input("One-time implementation cost", min_value=0.0, value=0.0, step=500.0)
    requested_date = st.date_input("Date originally requested", value=date(date.today().year - 1, date.today().month, 1))
    show_prep_cost = st.toggle("Include prep hours in total cost", value=True)

    st.markdown("---")
    st.header("Upload replacement CSVs")
    salary_upload = st.file_uploader(
        "Upload salary table CSV",
        type=["csv"],
        help="Optional. Replaces the default salary table for the current session.",
    )
    meeting_upload = st.file_uploader(
        "Upload meeting log CSV",
        type=["csv"],
        help="Optional. Replaces the default meeting log for the current session.",
    )

    st.markdown("---")
    st.caption("You can upload replacement CSVs or edit the tables directly in the app.")

salary_df = load_uploaded_or_default(salary_upload, DATA_DIR / "salary_table.csv")
meetings_df = load_uploaded_or_default(meeting_upload, DATA_DIR / "meetings.csv")

salary_calc_df = clean_salary_table(salary_df.copy())
roles = salary_calc_df["role"].astype(str).tolist()
meeting_calc_df = clean_meeting_table(meetings_df.copy(), roles)

with st.expander("Edit salary table", expanded=False):
    st.caption("You can edit the current working salary table here.")
    edited_salary_df = st.data_editor(
        salary_df,
        use_container_width=True,
        num_rows="dynamic",
        key="salary_editor",
    )
    salary_calc_df = clean_salary_table(edited_salary_df)
    roles = salary_calc_df["role"].astype(str).tolist()

with st.expander("Edit meeting log", expanded=False):
    st.caption("You can edit the current working meeting log here.")
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
months_since_request = months_between(requested_date, date.today())
roi_pct = ((total_cost - solution_total) / solution_total * 100) if solution_total > 0 else 0.0

top_left, top_right = st.columns([1.25, 1])

with top_left:
    animated_currency_card("Total Cost of Meetings", total_cost, height=165)

with top_right:
    st.markdown(
        f"""
        <div class="hero-card" style="min-height:165px;">
            <div class="hero-label">Solution Cost (Physical Cost)</div>
            <div style="color:#173f8a; font-size:1.2rem; margin-bottom:10px;">Annual cost of {solution_name}</div>
            <div style="color:#1746a2; font-size:3rem; font-weight:800; line-height:1.0;">{money(solution_total)}</div>
            <div style="color:#1746a2; font-size:1.2rem; font-weight:600; margin-top:6px;">per year</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Cost multiple</div>
            <div class="kpi-number">{comparison['cost_multiple']:.1f}x</div>
            <div class="kpi-support">times the cost of the solution</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Months since request</div>
            <div class="kpi-number">{months_since_request}</div>
            <div class="kpi-support">months of delay tracked</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Meetings logged</div>
            <div class="kpi-number">{int(metrics['total_meetings'])}</div>
            <div class="kpi-support">total meetings in the model</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total hours</div>
            <div class="kpi-number">{metrics['total_hours']:.1f}</div>
            <div class="kpi-support">meeting hours counted</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

main_left, main_right = st.columns([1.05, 1.15], gap="large")

with main_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Average salary table")
    display_salary = salary_calc_df[["role", "annual_salary", "loaded_hourly_rate"]].copy()
    display_salary.columns = ["Role", "Average Salary", "Loaded Hourly Rate"]
    display_salary["Average Salary"] = display_salary["Average Salary"].map(lambda x: money(float(x)))
    display_salary["Loaded Hourly Rate"] = display_salary["Loaded Hourly Rate"].map(lambda x: f"${float(x):,.2f}")
    st.dataframe(display_salary, use_container_width=True, hide_index=True)
    st.caption("*Loaded hourly rate includes benefits and overhead based on 2,080 hours per year.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Meetings input")
    display_cols = ["meeting_name", "meeting_date", "number_of_meetings"] + [r for r in roles if r in meeting_calc_df.columns]
    if not meeting_calc_df.empty:
        display_meetings = meeting_calc_df[display_cols].copy()
        display_meetings.columns = [c.replace("_", " ").title() for c in display_meetings.columns]
        st.dataframe(display_meetings, use_container_width=True, hide_index=True)
    else:
        st.info("No meeting rows available yet.")
    st.markdown('</div>', unsafe_allow_html=True)

with main_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Total cost of meetings")
    if not result_df.empty:
        hero_a, hero_b = st.columns([1.25, 0.9])

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
    else:
        st.info("Add meetings to generate the dashboard view.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Cumulative cost over time")
    if not result_df.empty and "meeting_date" in result_df.columns:
        plot_df = result_df.dropna(subset=["meeting_date"]).copy()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(plot_df["meeting_date"], plot_df["cumulative_cost"], marker="o")
        ax.set_xlabel("")
        ax.set_ylabel("Cost ($)")
        ax.ticklabel_format(style="plain", axis="y")
        st.pyplot(fig)
    else:
        st.info("Add meeting dates to display the cumulative trend chart.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="banner-box">
        <div class="banner-title">Stop the drain. Approve the solution.</div>
        <div class="banner-text">
            You have spent {money(total_cost)} discussing a solution that costs {money(solution_total)}.
            Estimated return on investment: {roi_pct:,.0f}%.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

bottom_left, bottom_right = st.columns([1.05, 1.15], gap="large")

with bottom_left:
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
    if existing_cols:
        show_df = result_df[existing_cols].copy()
        st.dataframe(show_df, use_container_width=True, hide_index=True)
    else:
        st.info("Meeting calculations will appear here.")

with bottom_right:
    st.subheader("Cost by role")
    if not role_summary_df.empty:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(role_summary_df["role"], role_summary_df["cost"])
        ax2.set_xlabel("")
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
