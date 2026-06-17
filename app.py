import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import os

st.set_page_config(
    page_title="NovaPharma | Onconova LOE Command",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anek+Bangla:wght@400;500;600;700&family=Sora:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    background-color: #FFFFFF;
}

.main { background-color: #FFFFFF; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; background-color: #FFFFFF; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D558B 0%, #1171B9 100%);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] .stRadio label { 
    color: #FFFFFF !important; 
    font-family: 'Sora', sans-serif;
    font-size: 0.88rem;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }

/* Header */
.dash-header {
    background: linear-gradient(135deg, #0D558B 0%, #1171B9 60%, #51ADEF 100%);
    padding: 1.4rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.8rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(17,113,185,0.18);
}
.header-left h1 {
    font-family: 'Anek Bangla', sans-serif;
    color: #FFFFFF;
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0 0 4px 0;
    letter-spacing: 0.3px;
}
.header-left p {
    color: rgba(255,255,255,0.78);
    font-size: 0.82rem;
    margin: 0;
    font-family: 'Sora', sans-serif;
}
.loe-box {
    background: rgba(255,255,255,0.12);
    border: 1.5px solid rgba(255,255,255,0.3);
    border-radius: 10px;
    padding: 0.8rem 1.6rem;
    text-align: center;
}
.loe-num {
    font-family: 'Anek Bangla', sans-serif;
    color: #FFFFFF;
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1;
    display: block;
}
.loe-label {
    color: rgba(255,255,255,0.75);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-family: 'Sora', sans-serif;
    display: block;
    margin-top: 3px;
}
.loe-sub {
    color: rgba(255,255,255,0.6);
    font-size: 0.72rem;
    font-family: 'Sora', sans-serif;
    display: block;
    margin-top: 2px;
}

/* KPI Cards — white, clean, no colored borders */
.kpi-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    border: 1px solid #E8EDF2;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    height: 100%;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1171B9, #51ADEF);
    border-radius: 10px 10px 0 0;
}
.kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 0.5rem;
    display: block;
}
.kpi-num {
    font-family: 'Anek Bangla', sans-serif;
    font-size: 1.9rem;
    font-weight: 700;
    color: #0D558B;
    margin: 0;
    line-height: 1.1;
    display: block;
}
.kpi-label {
    font-size: 0.72rem;
    color: #666666;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-family: 'Sora', sans-serif;
    font-weight: 500;
    margin: 0 0 4px 0;
    display: block;
}
.kpi-delta {
    font-size: 0.78rem;
    margin-top: 0.3rem;
    font-family: 'Sora', sans-serif;
    display: block;
}
.delta-up { color: #2E7D32; }
.delta-down { color: #C62828; }
.delta-warn { color: #E65100; }
.delta-neutral { color: #666666; }

/* Section headers */
.sec-head {
    font-family: 'Anek Bangla', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #0D558B;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #E8EDF2;
    margin-bottom: 1rem;
    letter-spacing: 0.2px;
}

/* Alert cards */
.alert-card {
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    border: 1px solid transparent;
}
.alert-urgent   { background: #FFF8F8; border-color: #FFCDD2; }
.alert-warning  { background: #FFFDE7; border-color: #FFF176; }
.alert-oppty    { background: #F1F8E9; border-color: #DCEDC8; }
.alert-insight  { background: #F0F7FF; border-color: #BBDEFB; }

.alert-type {
    font-family: 'Anek Bangla', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
.alert-msg {
    font-family: 'Sora', sans-serif;
    font-size: 0.85rem;
    color: #333333;
    margin: 0.35rem 0 0.25rem 0;
    line-height: 1.5;
}
.alert-action {
    font-family: 'Sora', sans-serif;
    font-size: 0.82rem;
    color: #0D558B;
    font-weight: 500;
}
.alert-meta {
    font-family: 'Sora', sans-serif;
    font-size: 0.75rem;
    color: #666666;
    margin-top: 0.2rem;
}

/* Info pill */
.info-pill {
    display: inline-block;
    background: #EEF5FC;
    color: #0D558B;
    font-family: 'Sora', sans-serif;
    font-size: 0.76rem;
    font-weight: 500;
    padding: 4px 12px;
    border-radius: 20px;
    margin-right: 6px;
    margin-bottom: 6px;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── COLORS ────────────────────────────────────────────────────────────────────
C_PRIMARY   = "#1171B9"
C_DARK      = "#0D558B"
C_LIGHT     = "#51ADEF"
C_NEUTRAL   = "#666666"
C_RED       = "#C62828"
C_AMBER     = "#E65100"
C_GREEN     = "#2E7D32"
C_RED_L     = "#EF9A9A"
C_AMBER_L   = "#FFCC80"
C_GREEN_L   = "#A5D6A7"
C_BLUE_L    = "#BBDEFB"
CHART_SEQ   = [C_DARK, C_PRIMARY, C_LIGHT, "#90CAF9", "#64B5F6", "#42A5F5"]

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "data")
    return {
        "reps":     pd.read_csv(f"{base}/reps.csv"),
        "hcps":     pd.read_csv(f"{base}/hcps.csv"),
        "patients": pd.read_csv(f"{base}/patients.csv"),
        "revenue":  pd.read_csv(f"{base}/revenue_monthly.csv"),
        "drivers":  pd.read_csv(f"{base}/erosion_drivers.csv"),
        "comp":     pd.read_csv(f"{base}/competitive_intel.csv"),
        "alerts":   pd.read_csv(f"{base}/ai_alerts.csv"),
    }

data    = load_data()
reps     = data["reps"]
hcps     = data["hcps"]
patients = data["patients"]
revenue  = data["revenue"]
drivers  = data["drivers"]
comp     = data["comp"]
alerts   = data["alerts"]

loe_date    = date(2027, 11, 1)
days_to_loe = (loe_date - date.today()).days

# ── CHART THEME ───────────────────────────────────────────────────────────────
def chart_layout(fig, height=300):
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Sora, sans-serif", color="#333333", size=11),
        legend=dict(font=dict(size=10)),
        xaxis=dict(gridcolor="#F0F0F0", linecolor="#E0E0E0"),
        yaxis=dict(gridcolor="#F0F0F0", linecolor="#E0E0E0"),
    )
    return fig

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 💊 NovaPharma")
    st.markdown("**Onconova LOE Command**")
    st.markdown("---")
    page = st.radio("", [
        "🏠  Executive Overview",
        "👥  Rep Management",
        "🩺  HCP Retention",
        "🧑‍⚕️  Patient Retention",
        "📉  Erosion Drivers",
        "🏁  Competitive Intel",
        "🤖  AI Agent Insights",
    ])
    st.markdown("---")
    st.markdown(f"**LOE Date** · Nov 1, 2027")
    st.markdown(f"**Days to LOE** · `{days_to_loe}`")
    st.markdown(f"**User** · James Whitfield")
    st.markdown(f"**Role** · VP Brand")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <div class="header-left">
    <h1>💊 Onconova LOE Command Dashboard</h1>
    <p>NovaPharma &nbsp;·&nbsp; VP Brand View &nbsp;·&nbsp; James Whitfield &nbsp;·&nbsp; {datetime.today().strftime('%B %d, %Y')}</p>
  </div>
  <div class="loe-box">
    <span class="loe-num">{days_to_loe}</span>
    <span class="loe-label">Days to LOE</span>
    <span class="loe-sub">November 2027</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Executive Overview":

    latest_rev       = revenue[revenue["month"] <= "2025-10"].iloc[-1]
    active_patients  = len(patients[~patients["discontinuation_flag"]])
    high_risk_pat    = len(patients[patients["switch_risk_category"] == "High"])
    tier1_hcps       = len(hcps[hcps["segment"] == "Tier 1"])
    high_risk_hcps   = len(hcps[hcps["flight_risk"] == "High"])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    cards = [
        (c1, "💰", "Monthly Revenue",     f"${latest_rev['actual_revenue_m']:.0f}M", "▲ +4.2% vs forecast", "delta-up"),
        (c2, "👤", "Active Patients",      f"{active_patients:,}",                   "~6% monthly churn", "delta-warn"),
        (c3, "⚠️", "High Switch-Risk Pts", f"{high_risk_pat:,}",                     "Score > 65 — needs action", "delta-down"),
        (c4, "🧑‍💼","Sales Reps",           "220",                                    "Target 135 by Q3 '26", "delta-warn"),
        (c5, "🩺", "Tier 1 HCPs",          f"{tier1_hcps}",                          f"{high_risk_hcps} at flight risk", "delta-down"),
        (c6, "💊", "ANDA Filers",          "6",                                      "▲ 2 new this quarter", "delta-down"),
    ]
    for col, icon, label, num, delta, dcls in cards:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <span class="kpi-icon">{icon}</span>
              <span class="kpi-label">{label}</span>
              <span class="kpi-num">{num}</span>
              <span class="kpi-delta {dcls}">{delta}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<p class="sec-head">Revenue Trend & LOE Forecast (2022–2027)</p>', unsafe_allow_html=True)
        rev = revenue.copy()
        rev["month_dt"] = pd.to_datetime(rev["month"])
        fig = go.Figure()
        fig.add_vrect(x0="2027-11-01", x1=str(rev["month_dt"].max()),
                      fillcolor="#FFEBEE", opacity=0.5, layer="below", line_width=0)
        fig.add_vline(x="2027-11-01", line_dash="dash", line_color=C_RED, line_width=1.5,
                      annotation_text="LOE · Nov 2027", annotation_font_color=C_RED,
                      annotation_position="top right")
        fig.add_trace(go.Scatter(x=rev["month_dt"], y=rev["actual_revenue_m"],
                                 name="Actual Revenue", line=dict(color=C_DARK, width=2.5)))
        fig.add_trace(go.Scatter(x=rev["month_dt"], y=rev["forecast_revenue_m"],
                                 name="Forecast", line=dict(color=C_LIGHT, width=1.5, dash="dot")))
        fig.add_trace(go.Scatter(x=rev["month_dt"], y=rev["market_share_pct"],
                                 name="Market Share %", line=dict(color=C_AMBER, width=1.5, dash="dash"),
                                 yaxis="y2"))
        fig.update_layout(
            height=310, margin=dict(l=0,r=0,t=10,b=0),
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font=dict(family="Sora, sans-serif", size=11),
            legend=dict(orientation="h", y=1.1, font=dict(size=10)),
            yaxis=dict(title="Revenue ($M)", gridcolor="#F0F0F0"),
            yaxis2=dict(title="Market Share %", overlaying="y", side="right",
                        showgrid=False, range=[0, 100]),
            xaxis=dict(gridcolor="#F0F0F0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="sec-head">Revenue at Risk by Erosion Driver</p>', unsafe_allow_html=True)
        fig2 = px.bar(drivers.sort_values("revenue_at_risk_m"),
                      x="revenue_at_risk_m", y="driver", orientation="h",
                      color="revenue_at_risk_m",
                      color_continuous_scale=[C_BLUE_L, C_PRIMARY, C_RED],
                      labels={"revenue_at_risk_m": "$M at Risk", "driver": ""})
        fig2.update_layout(height=310, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                           coloraxis_showscale=False,
                           font=dict(family="Sora, sans-serif", size=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="sec-head">Top AI Agent Alerts</p>', unsafe_allow_html=True)
    a1, a2 = st.columns(2)
    top_alerts = alerts[alerts["type"].isin(["URGENT","WARNING"])].head(4)
    for i, (_, row) in enumerate(top_alerts.iterrows()):
        cls    = "alert-urgent" if row["type"] == "URGENT" else "alert-warning"
        color  = C_RED if row["type"] == "URGENT" else C_AMBER
        icon   = "🚨" if row["type"] == "URGENT" else "⚠️"
        with (a1 if i % 2 == 0 else a2):
            st.markdown(f"""
            <div class="alert-card {cls}">
              <span class="alert-type" style="color:{color}">{icon} {row['type']} · {row['module']}</span>
              <p class="alert-msg">{row['message']}</p>
              <p class="alert-action">→ {row['action']}</p>
              <p class="alert-meta">Revenue at risk · ${row['revenue_impact_k']:,}K</p>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — REP MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "👥  Rep Management":

    to_retain   = len(reps[reps["redeployment_recommendation"] == "Retain"])
    to_pipeline = len(reps[reps["redeployment_recommendation"].isin(["Pipeline Drug A","Pipeline Drug B"])])
    to_release  = len(reps[reps["redeployment_recommendation"] == "Release"])
    avg_perf    = reps["performance_score"].mean()

    c1,c2,c3,c4 = st.columns(4)
    cards = [
        (c1,"✅","Retain on Onconova",  f"{to_retain}",    "Core defense force through LOE","delta-up"),
        (c2,"🔄","Redeploy to Pipeline",f"{to_pipeline}",  "Move to Pipeline Drug A / B",   "delta-warn"),
        (c3,"📤","Release (Reduce)",    f"{to_release}",   "Target: complete by Q3 2026",   "delta-down"),
        (c4,"📊","Avg Performance Score",f"{avg_perf:.1f}","Out of 100",                    "delta-neutral"),
    ]
    for col, icon, label, num, delta, dcls in cards:
        with col:
            st.markdown(f"""<div class="kpi-card">
              <span class="kpi-icon">{icon}</span>
              <span class="kpi-label">{label}</span>
              <span class="kpi-num">{num}</span>
              <span class="kpi-delta {dcls}">{delta}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="sec-head">Rep Recommendation by Region</p>', unsafe_allow_html=True)
        region_summary = reps.groupby(["region","redeployment_recommendation"]).size().reset_index(name="count")
        color_map = {"Retain": C_GREEN, "Pipeline Drug A": C_PRIMARY,
                     "Pipeline Drug B": C_LIGHT, "Release": C_RED}
        fig = px.bar(region_summary, x="region", y="count",
                     color="redeployment_recommendation", color_discrete_map=color_map,
                     labels={"count":"Reps","region":"","redeployment_recommendation":"Action"})
        fig = chart_layout(fig, 300)
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="sec-head">Performance vs HCP Coverage</p>', unsafe_allow_html=True)
        fig2 = px.scatter(reps, x="performance_score", y="hcp_count_covered",
                          size="retention_score", color="redeployment_recommendation",
                          color_discrete_map=color_map,
                          hover_data=["first_name","last_name","territory","tenure_years"],
                          labels={"performance_score":"Performance Score (0–100)",
                                  "hcp_count_covered":"HCPs Covered","redeployment_recommendation":"Action"})
        fig2 = chart_layout(fig2, 300)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="sec-head">Rep-Level Decision Table</p>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1: region_f = st.selectbox("Region", ["All"] + sorted(reps["region"].unique().tolist()))
    with f2: rec_f    = st.selectbox("Recommendation", ["All"] + reps["redeployment_recommendation"].unique().tolist())
    with f3: perf_min = st.slider("Min Performance Score", 0, 100, 0)

    filt = reps.copy()
    if region_f != "All": filt = filt[filt["region"] == region_f]
    if rec_f    != "All": filt = filt[filt["redeployment_recommendation"] == rec_f]
    filt = filt[filt["performance_score"] >= perf_min]

    show = filt[["rep_id","first_name","last_name","region","territory",
                  "tenure_years","performance_score","hcp_count_covered",
                  "retention_score","redeployment_recommendation","pipeline_fit"]].copy()
    show.columns = ["ID","First","Last","Region","Territory","Tenure(yrs)",
                    "Perf Score","HCPs","Retention Score","Recommendation","Pipeline Fit"]
    st.dataframe(show.sort_values("Retention Score", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=340)
    st.caption(f"Showing {len(filt)} of 220 reps  ·  Sort by Retention Score ascending to find top reduction candidates")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — HCP RETENTION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🩺  HCP Retention":

    tier1      = hcps[hcps["segment"] == "Tier 1"]
    high_risk  = hcps[hcps["flight_risk"] == "High"]
    msl_on     = hcps[hcps["msl_engaged"] == True]
    avg_loyal  = hcps["loyalty_score"].mean()

    c1,c2,c3,c4 = st.columns(4)
    for col, icon, label, num, delta, dcls in [
        (c1,"🏆","Tier 1 HCPs",          f"{len(tier1)}",   "Drive 65% of total Rx volume","delta-up"),
        (c2,"🚨","High Flight Risk HCPs", f"{len(high_risk)}","Loyalty score < 45",         "delta-down"),
        (c3,"🤝","MSL-Engaged HCPs",      f"{len(msl_on)}",  "Active MSL relationship",     "delta-up"),
        (c4,"💙","Avg Loyalty Score",      f"{avg_loyal:.1f}","Out of 100",                  "delta-neutral"),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
              <span class="kpi-icon">{icon}</span>
              <span class="kpi-label">{label}</span>
              <span class="kpi-num">{num}</span>
              <span class="kpi-delta {dcls}">{delta}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="sec-head">HCP Segment Distribution</p>', unsafe_allow_html=True)
        seg = hcps["segment"].value_counts().reset_index()
        seg.columns = ["Segment","Count"]
        fig = px.pie(seg, names="Segment", values="Count",
                     color_discrete_sequence=[C_DARK, C_PRIMARY, C_LIGHT],
                     hole=0.45)
        fig.update_traces(textfont=dict(family="Sora, sans-serif", size=11))
        fig.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0),
                          paper_bgcolor="#FFFFFF",
                          font=dict(family="Sora, sans-serif"),
                          legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="sec-head">Flight Risk by Region</p>', unsafe_allow_html=True)
        risk_r = hcps.groupby(["region","flight_risk"]).size().reset_index(name="count")
        fig2 = px.bar(risk_r, x="region", y="count", color="flight_risk",
                      color_discrete_map={"High": C_RED, "Medium": C_AMBER, "Low": C_GREEN},
                      labels={"count":"HCPs","region":"","flight_risk":"Flight Risk"})
        fig2 = chart_layout(fig2, 280)
        fig2.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="sec-head">HCP Priority Matrix — Loyalty Score vs Monthly Rx Volume</p>', unsafe_allow_html=True)
    st.caption("Top-right quadrant (high loyalty + high Rx) = Protect at all costs · Bottom-right (low loyalty + high Rx) = Urgent MSL intervention")
    fig3 = px.scatter(hcps, x="loyalty_score", y="monthly_rx_volume",
                      color="flight_risk", size="total_active_patients",
                      color_discrete_map={"High": C_RED, "Medium": C_AMBER, "Low": C_GREEN},
                      hover_data=["first_name","last_name","specialty","territory","formulary_status"],
                      labels={"loyalty_score":"Loyalty Score (0–100)",
                              "monthly_rx_volume":"Monthly Rx Volume","flight_risk":"Flight Risk"})
    fig3.add_vline(x=65, line_dash="dash", line_color=C_NEUTRAL, line_width=1,
                   annotation_text="Retention Threshold", annotation_font_color=C_NEUTRAL)
    fig3.add_hline(y=80, line_dash="dash", line_color=C_NEUTRAL, line_width=1,
                   annotation_text="High-Volume Threshold", annotation_font_color=C_NEUTRAL)
    fig3 = chart_layout(fig3, 360)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<p class="sec-head">HCP Filter & Detail Table</p>', unsafe_allow_html=True)
    f1, f2 = st.columns(2)
    with f1: risk_f = st.selectbox("Flight Risk", ["All","High","Medium","Low"])
    with f2: seg_f  = st.selectbox("Segment", ["All","Tier 1","Tier 2","Tier 3"])
    filt_h = hcps.copy()
    if risk_f != "All": filt_h = filt_h[filt_h["flight_risk"] == risk_f]
    if seg_f  != "All": filt_h = filt_h[filt_h["segment"] == seg_f]
    show_h = filt_h[["hcp_id","first_name","last_name","specialty","region",
                       "monthly_rx_volume","loyalty_score","flight_risk","segment",
                       "msl_engaged","formulary_status","last_rep_call_days_ago"]].copy()
    show_h.columns = ["ID","First","Last","Specialty","Region","Monthly Rx",
                       "Loyalty","Flight Risk","Segment","MSL Engaged","Formulary","Days Since Call"]
    st.dataframe(show_h.sort_values("Monthly Rx", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=320)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — PATIENT RETENTION
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🧑‍⚕️  Patient Retention":

    active     = patients[~patients["discontinuation_flag"]]
    high_sw    = patients[patients["switch_risk_category"] == "High"]
    no_copay   = patients[(patients["switch_risk_category"] == "High") & (~patients["copay_assist_enrolled"])]
    avg_adh    = patients["adherence_rate_pct"].mean()

    c1,c2,c3,c4 = st.columns(4)
    for col, icon, label, num, delta, dcls in [
        (c1,"💊","Active Patients",           f"{len(active):,}",  "On active Onconova therapy",        "delta-up"),
        (c2,"⚠️","High Switch-Risk Patients",  f"{len(high_sw):,}", "Likely to switch at generic entry", "delta-down"),
        (c3,"🚨","High Risk — No Copay Assist",f"{len(no_copay):,}","Immediate outreach required",       "delta-down"),
        (c4,"📈","Avg Adherence Rate",          f"{avg_adh:.1f}%",  "Target ≥ 85%",                      "delta-warn"),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
              <span class="kpi-icon">{icon}</span>
              <span class="kpi-label">{label}</span>
              <span class="kpi-num">{num}</span>
              <span class="kpi-delta {dcls}">{delta}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<p class="sec-head">Switch Risk Distribution</p>', unsafe_allow_html=True)
        rd = patients["switch_risk_category"].value_counts().reset_index()
        rd.columns = ["Risk","Patients"]
        fig = px.pie(rd, names="Risk", values="Patients", hole=0.45,
                     color="Risk", color_discrete_map={"High":C_RED,"Medium":C_AMBER,"Low":C_GREEN})
        fig.update_layout(height=260, margin=dict(l=0,r=0,t=10,b=0),
                          paper_bgcolor="#FFFFFF", font=dict(family="Sora, sans-serif"),
                          legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<p class="sec-head">Patients by Specialty Pharmacy</p>', unsafe_allow_html=True)
        sp = patients.groupby("specialty_pharmacy").size().reset_index(name="patients").sort_values("patients")
        fig2 = px.bar(sp, x="patients", y="specialty_pharmacy", orientation="h",
                      color_discrete_sequence=[C_PRIMARY],
                      labels={"patients":"Patients","specialty_pharmacy":""})
        fig2 = chart_layout(fig2, 260)
        st.plotly_chart(fig2, use_container_width=True)

    with c3:
        st.markdown('<p class="sec-head">Switch Risk by Insurance Type</p>', unsafe_allow_html=True)
        ins = patients.groupby(["insurance_type","switch_risk_category"]).size().reset_index(name="count")
        fig3 = px.bar(ins, x="insurance_type", y="count", color="switch_risk_category",
                      color_discrete_map={"High":C_RED,"Medium":C_AMBER,"Low":C_GREEN},
                      labels={"insurance_type":"","count":"Patients","switch_risk_category":"Risk"})
        fig3 = chart_layout(fig3, 260)
        fig3.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<p class="sec-head">Patient Retention Action Priorities</p>', unsafe_allow_html=True)
    low_supply = len(patients[patients["days_supply_remaining"] < 7])
    low_adh    = len(patients[patients["adherence_rate_pct"] < 75])
    medicare   = len(patients[patients["insurance_type"] == "Medicare Part D"])
    actions = pd.DataFrame([
        {"Priority":"🔴  1","Action":"Enroll high-risk patients not on copay assist program","Patients Impacted":f"{len(no_copay):,}","Owner":"Patient Support Hub","Timeline":"Immediate"},
        {"Priority":"🔴  2","Action":"Outreach to patients with < 7 days supply remaining","Patients Impacted":f"{low_supply:,}","Owner":"Specialty Pharmacy + Hub","Timeline":"This week"},
        {"Priority":"🟡  3","Action":"Enroll low-adherence patients (< 75%) in nurse support","Patients Impacted":f"{low_adh:,}","Owner":"Nurse Support Team","Timeline":"30 days"},
        {"Priority":"🟡  4","Action":"Proactive LOE communication to Medicare Part D patients","Patients Impacted":f"{medicare:,}","Owner":"Marketing + Patient Hub","Timeline":"Q1 2026"},
    ])
    st.dataframe(actions, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — EROSION DRIVERS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "📉  Erosion Drivers":

    total_risk = drivers["revenue_at_risk_m"].sum()
    st.markdown(f"""<div class="kpi-card" style="margin-bottom:1.5rem">
      <span class="kpi-icon">💸</span>
      <span class="kpi-label">Total Revenue at Risk Across All Drivers</span>
      <span class="kpi-num">${total_risk:,}M</span>
      <span class="kpi-delta delta-down">Requires coordinated defense plan across Commercial, Market Access, Medical & Patient teams</span>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="sec-head">Impact Score by Driver</p>', unsafe_allow_html=True)
        fig = px.bar(drivers.sort_values("impact_score"),
                     x="impact_score", y="driver", orientation="h",
                     color="category",
                     color_discrete_sequence=CHART_SEQ,
                     labels={"impact_score":"Impact Score (0–100)","driver":"","category":"Category"})
        fig = chart_layout(fig, 320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="sec-head">Revenue at Risk ($M)</p>', unsafe_allow_html=True)
        fig2 = px.bar(drivers.sort_values("revenue_at_risk_m"),
                      x="revenue_at_risk_m", y="driver", orientation="h",
                      color="revenue_at_risk_m",
                      color_continuous_scale=[C_BLUE_L, C_PRIMARY, C_RED],
                      labels={"revenue_at_risk_m":"Revenue at Risk ($M)","driver":""})
        fig2 = chart_layout(fig2, 320)
        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="sec-head">Full Action Plan by Driver</p>', unsafe_allow_html=True)
    for _, row in drivers.sort_values("impact_score", ascending=False).iterrows():
        s = row["impact_score"]
        icon = "🔴" if s >= 70 else ("🟡" if s >= 50 else "🟢")
        with st.expander(f"{icon}  {row['driver']}  —  Impact: {s}/100  ·  Revenue at Risk: ${row['revenue_at_risk_m']}M"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Category:** {row['category']}")
                st.markdown(f"**Current Status:** {row['current_status']}")
                st.markdown(f"**Action Owner:** {row['action_owner']}")
            with c2:
                st.markdown(f"**Recommended Action:** {row['recommended_action']}")
                st.markdown(f"**Timeline:** {row['timeline']}")
                st.markdown(f"**Revenue at Risk:** ${row['revenue_at_risk_m']}M")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — COMPETITIVE INTEL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏁  Competitive Intel":

    generics = comp[comp["type"] == "Generic"]
    branded  = comp[comp["type"] == "Branded Competitor"]

    c1,c2,c3,c4 = st.columns(4)
    for col, icon, label, num, delta, dcls in [
        (c1,"📄","ANDA Filers (Generic)",      f"{len(generics)}",                                 "▲ 2 new this quarter",              "delta-down"),
        (c2,"🏭","Branded Competitors",         f"{len(branded)}",                                  "In Phase 3 — ETA 2026–2027",        "delta-warn"),
        (c3,"💲","Avg Generic Price Discount",  f"{generics['price_discount_pct'].mean():.0f}%",    "vs Onconova branded price",         "delta-down"),
        (c4,"📉","Combined Mkt Share Risk Y1",  f"{comp['market_share_forecast_y1'].sum():.0f}%",   "Total projected loss at LOE",       "delta-down"),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
              <span class="kpi-icon">{icon}</span>
              <span class="kpi-label">{label}</span>
              <span class="kpi-num">{num}</span>
              <span class="kpi-delta {dcls}">{delta}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="sec-head">Projected Y1 Market Share by Competitor</p>', unsafe_allow_html=True)
        fig = px.bar(comp.sort_values("market_share_forecast_y1", ascending=False),
                     x="company", y="market_share_forecast_y1", color="type",
                     color_discrete_map={"Generic": C_RED, "Branded Competitor": C_AMBER},
                     labels={"market_share_forecast_y1":"Projected Mkt Share Y1 (%)","company":"","type":"Type"})
        fig = chart_layout(fig, 300)
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="sec-head">Generic Price Discount vs Market Share Threat</p>', unsafe_allow_html=True)
        fig2 = px.scatter(generics, x="price_discount_pct", y="market_share_forecast_y1",
                          text="company", size="market_share_forecast_y1",
                          color_discrete_sequence=[C_RED],
                          labels={"price_discount_pct":"Price Discount vs Branded (%)","market_share_forecast_y1":"Forecast Mkt Share Y1 (%)"})
        fig2.update_traces(textposition="top center", textfont=dict(size=9))
        fig2 = chart_layout(fig2, 300)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="sec-head">Competitive Threat Summary</p>', unsafe_allow_html=True)
    dc = comp[["company","type","anda_status","est_launch_date",
               "price_discount_pct","market_share_forecast_y1","threat_level"]].copy()
    dc.columns = ["Company","Type","Status","Est. Launch","Price Discount %","Forecast Mkt Share Y1 %","Threat Level"]
    st.dataframe(dc, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — AI AGENT INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🤖  AI Agent Insights":

    st.markdown(f'<p class="sec-head">AI Agent — Auto-Generated Alerts & Recommendations</p>', unsafe_allow_html=True)
    st.caption(f"Last updated · {datetime.today().strftime('%B %d, %Y at %I:%M %p')}  ·  Next refresh · Tomorrow 6:00 AM")

    st.markdown("<br>", unsafe_allow_html=True)
    urg = len(alerts[alerts["type"]=="URGENT"])
    wrn = len(alerts[alerts["type"]=="WARNING"])
    opp = len(alerts[alerts["type"]=="OPPORTUNITY"])
    ins = len(alerts[alerts["type"]=="INSIGHT"])

    c1,c2,c3,c4 = st.columns(4)
    for col, icon, label, num, delta, dcls in [
        (c1,"🚨","Urgent Actions",  f"{urg}", "Act within 48 hours", "delta-down"),
        (c2,"⚠️","Warnings",        f"{wrn}", "Act this week",       "delta-warn"),
        (c3,"✅","Opportunities",   f"{opp}", "Capture this month",  "delta-up"),
        (c4,"💡","Insights",        f"{ins}", "For your awareness",  "delta-neutral"),
    ]:
        with col:
            st.markdown(f"""<div class="kpi-card">
              <span class="kpi-icon">{icon}</span>
              <span class="kpi-label">{label}</span>
              <span class="kpi-num">{num}</span>
              <span class="kpi-delta {dcls}">{delta}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        type_f = st.selectbox("Filter by Alert Type", ["All","URGENT","WARNING","OPPORTUNITY","INSIGHT"])
    total_risk = alerts["revenue_impact_k"].sum()
    st.markdown(f"<span class='info-pill'>💸 Total Revenue at Stake: ${total_risk/1000:.1f}M</span>"
                f"<span class='info-pill'>📋 {len(alerts)} alerts active</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    filtered_alerts = alerts if type_f == "All" else alerts[alerts["type"] == type_f]

    for _, row in filtered_alerts.iterrows():
        t    = row["type"]
        cls  = {"URGENT":"alert-urgent","WARNING":"alert-warning",
                "OPPORTUNITY":"alert-oppty","INSIGHT":"alert-insight"}.get(t,"alert-insight")
        icon = {"URGENT":"🚨","WARNING":"⚠️","OPPORTUNITY":"✅","INSIGHT":"💡"}.get(t,"ℹ️")
        color= {"URGENT":C_RED,"WARNING":C_AMBER,"OPPORTUNITY":C_GREEN,"INSIGHT":C_PRIMARY}.get(t,C_PRIMARY)
        st.markdown(f"""
        <div class="alert-card {cls}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <span class="alert-type" style="color:{color}">{icon} {t} &nbsp;·&nbsp; {row['module']}</span>
            <span class="alert-meta">${row['revenue_impact_k']:,}K at risk &nbsp;·&nbsp; {row['date']}</span>
          </div>
          <p class="alert-msg">{row['message']}</p>
          <p class="alert-action">→ {row['action']}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="sec-head">Revenue at Risk by Module</p>', unsafe_allow_html=True)
    mod = alerts.groupby("module")["revenue_impact_k"].sum().reset_index()
    fig = px.bar(mod.sort_values("revenue_impact_k"), x="revenue_impact_k", y="module",
                 orientation="h", color_discrete_sequence=[C_PRIMARY],
                 labels={"revenue_impact_k":"Revenue at Risk ($K)","module":""})
    fig = chart_layout(fig, 280)
    st.plotly_chart(fig, use_container_width=True)
