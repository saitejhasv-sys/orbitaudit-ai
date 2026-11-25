import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="OrbitAudit AI | Orbital Escrow Verification", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv("strr_predictions.csv")

df = load_data()
latest_epoch = sorted(df["epoch"].unique())[-1]
latest_df = df[df["epoch"] == latest_epoch].copy()

# Header
st.title("🛰️ OrbitAudit AI — Orbital Infrastructure Escrow & Milestone Tracker")
st.caption("Multi-Sensor Fusion (Sentinel-1 SAR Radar + Sentinel-2 Optical) | Corridor: Bengaluru STRR (NH-648)")

# Top Sidebar: Financial Escrow Inputs
st.sidebar.header("🏦 Infra-Lender Escrow Controls")
total_loan_cr = st.sidebar.number_input("Total Sanctioned Loan (₹ Crores)", min_value=50, max_value=2000, value=240, step=10)
manual_audit_cost_lakhs = st.sidebar.slider("Quarterly Field Audit Cost (₹ Lakhs)", 5, 50, 22)

avg_completion = latest_df["predicted_completion_pct"].mean()
stalled_count = (latest_df["status"] == "Stalled").sum()
delayed_count = (latest_df["status"] == "Delayed").sum()

# Calculate Escrow Release vs. Hold
segment_budget = total_loan_cr / len(latest_df)
released_cr = 0.0
held_cr = 0.0
for _, row in latest_df.iterrows():
    earned = segment_budget * (row["predicted_completion_pct"] / 100.0)
    expected = segment_budget * (row["expected_pct"] / 100.0)
    released_cr += earned
    if row["status"] in ["Stalled", "Delayed"]:
        held_cr += max(0.0, expected - earned)

annual_audit_savings = round(manual_audit_cost_lakhs * 4 * 0.72, 1)

# KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("AI-Verified Progress", f"{avg_completion:.1f}%", f"Epoch: {latest_epoch}")
k2.metric("At-Risk Segments", f"{stalled_count} Stalled | {delayed_count} Delayed", delta_color="inverse")
k3.metric("Recommended Release", f"₹{released_cr:.1f} Cr", f"Out of ₹{total_loan_cr} Cr")
k4.metric("Escrow Held Back", f"₹{held_cr:.1f} Cr", f"Saves ₹{annual_audit_savings}L/yr in audits")

st.divider()

# Main Layout: Map (Left) + Segment Inspector (Right)
col_map, col_detail = st.columns([1.15, 1.0])

with col_map:
    st.subheader("Live Corridor Verification Map (Bengaluru STRR)")
    color_map = {"On Track": "#16a34a", "Delayed": "#f59e0b", "Stalled": "#dc2626"}
    ordered_df = latest_df.sort_values("segment_id")

    fig_map = px.scatter_map(
        ordered_df,
        lat="lat",
        lon="lon",
        color="status",
        size="predicted_completion_pct",
        size_max=24,
        color_discrete_map=color_map,
        hover_name="segment_name",
        hover_data={
            "segment_id": True,
            "predicted_completion_pct": True,
            "expected_pct": True,
            "sar_vv_db": True,
            "ndbi": True,
            "lat": False,
            "lon": False,
        },
        center={"lat": 13.165, "lon": 77.765},
        zoom=10.3,
        height=460,
    )
    # Draw highway corridor alignment connecting all 6 STRR segments
    fig_map.add_trace(
        go.Scattermap(
            lat=ordered_df["lat"],
            lon=ordered_df["lon"],
            mode="lines+text",
            line=dict(width=3, color="#475569"),
            text=ordered_df["segment_id"],
            textposition="top right",
            showlegend=False,
        )
    )
    fig_map.update_layout(
        map_style="carto-positron",
        map_center={"lat": 13.165, "lon": 77.765},
        map_zoom=10.3,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(fig_map, use_container_width=True)

with col_detail:
    st.subheader("Segment Multi-Sensor Telemetry & Escrow Decision")
    selected_name = st.selectbox("Select Highway Segment:", latest_df["segment_name"].tolist())
    seg_hist = df[df["segment_name"] == selected_name].sort_values("epoch")
    seg_now = seg_hist.iloc[-1]

    # Dual-axis chart: Optical NDBI (concrete/soil) vs. SAR VV Radar (structures)
    fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
    fig_ts.add_trace(
        go.Scatter(x=seg_hist["epoch"], y=seg_hist["ndbi"], name="Optical Built-Up (NDBI)", line=dict(color="#2563eb", width=3)),
        secondary_y=False,
    )
    fig_ts.add_trace(
        go.Scatter(x=seg_hist["epoch"], y=seg_hist["sar_vv_db"], name="SAR Radar Backscatter (VV dB)", line=dict(color="#ea580c", width=3, dash="dot")),
        secondary_y=True,
    )
    fig_ts.update_layout(height=280, margin=dict(l=10, r=10, t=25, b=10), legend=dict(orientation="h", y=1.15))
    fig_ts.update_yaxes(title_text="Optical NDBI", secondary_y=False)
    fig_ts.update_yaxes(title_text="Radar VV (dB)", secondary_y=True)
    st.plotly_chart(fig_ts, use_container_width=True)

    # Automated Loan Decision Banner
    if seg_now["status"] == "On Track":
        st.success(f"**ACTION: APPROVE TRANCHE RELEASE** — Verified **{seg_now['predicted_completion_pct']}%** complete (Target: {seg_now['expected_pct']}%).")
    elif seg_now["status"] == "Delayed":
        st.warning(f"**ACTION: PARTIAL HOLD / WARNING** — Verified **{seg_now['predicted_completion_pct']}%** vs. {seg_now['expected_pct']}% target ({seg_now['schedule_gap_pct']}% gap).")
    else:
        st.error(f"**ACTION: FREEZE ESCROW TRANCHE** — Stalled at **{seg_now['predicted_completion_pct']}%** vs. {seg_now['expected_pct']}% target. Trigger drone/site audit.")

# Bottom Table & Model Proof
st.divider()
tab1, tab2 = st.tabs(["📋 Segment Audit Ledger", "📊 AI Model Validation (SAR+Optical vs. Optical-Only)"])

with tab1:
    display_cols = ["segment_id", "segment_name", "predicted_completion_pct", "expected_pct", "schedule_gap_pct", "status", "ndvi", "ndbi", "sar_vv_db"]
    st.dataframe(latest_df[display_cols], use_container_width=True, hide_index=True)

with tab2:
    c_img, c_txt = st.columns([1.2, 1])
    with c_img:
        st.image("validation_chart.png", caption="5-Fold Cross-Validation Error Comparison")
    with c_txt:
        st.markdown("""
        **Why Sensor Fusion Wins for Aerospace & Infra Judging:**
        * **Monsoon Cloud Immunity:** Sentinel-2 optical indices fail during heavy cloud cover; Sentinel-1 C-band SAR penetrates clouds day and night.
        * **Vertical Structure Detection:** Optical cameras confuse bare dirt with finished overpasses; SAR double-bounce backscatter (`VV/VH`) spikes specifically when concrete piers and steel girders rise.
        """)