import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="OrbitAudit AI | Orbital Escrow Command",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #060913 100%);
        color: #e2e8f0;
    }
    section[data-testid="stSidebar"] {
        background-color: #0b1120;
        border-right: 1px solid rgba(56, 189, 248, 0.18);
    }
    .hero-banner {
        background: linear-gradient(90deg, rgba(14,165,233,0.14) 0%, rgba(15,23,42,0.85) 100%);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-left: 5px solid #38bdf8;
        padding: 16px 22px;
        border-radius: 12px;
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: 0.4px;
        color: #f8fafc;
        margin: 0;
    }
    .hero-sub {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 4px;
    }
    .live-pill {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        margin-right: 8px;
    }
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }
    .audit-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 10px;
        padding: 14px 16px;
        font-size: 0.88rem;
        line-height: 1.55;
        color: #cbd5e1;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

df = pd.read_csv("strr_predictions.csv")
epochs = sorted(df["epoch"].unique())

st.markdown("""
<div class="hero-banner">
    <div><span class="live-pill">● ORBITAL TELEMETRY LOCKED</span> <span style="color:#38bdf8;font-size:0.8rem;font-weight:600;">SENTINEL-1 SAR + SENTINEL-2 MSI FUSION</span></div>
    <div class="hero-title">🛰️ OrbitAudit AI — Autonomous Infrastructure Escrow Verification</div>
    <div class="hero-sub">Corridor: Bengaluru Satellite Town Ring Road (NH-648 | Devanahalli – Hoskote) • WebGL 3D Corridor + Multi-Sensor Escrow Engine</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 🎛️ Mission & Escrow Parameters")
selected_epoch = st.sidebar.select_slider(
    "Orbital Time-Travel Epoch",
    options=epochs,
    value=epochs[-1],
)
total_loan_cr = st.sidebar.number_input("Sanctioned Infra Loan (₹ Crores)", min_value=50, max_value=2000, value=240, step=10)
manual_audit_cost_lakhs = st.sidebar.slider("Quarterly Manual Audit Cost (₹ Lakhs)", 5, 50, 22)

epoch_df = df[df["epoch"] == selected_epoch].sort_values("segment_id").reset_index(drop=True)

avg_completion = epoch_df["predicted_completion_pct"].mean()
stalled_count = (epoch_df["status"] == "Stalled").sum()
delayed_count = (epoch_df["status"] == "Delayed").sum()
ontrack_count = (epoch_df["status"] == "On Track").sum()

segment_budget = total_loan_cr / len(epoch_df)
released_cr = 0.0
held_cr = 0.0
for _, row in epoch_df.iterrows():
    earned = segment_budget * (row["predicted_completion_pct"] / 100.0)
    expected = segment_budget * (row["expected_pct"] / 100.0)
    released_cr += earned
    if row["status"] in ["Stalled", "Delayed"]:
        held_cr += max(0.0, expected - earned)

annual_audit_savings = round(manual_audit_cost_lakhs * 4 * 0.72, 1)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Orbital Verified Completion", f"{avg_completion:.1f}%", f"Pass: {selected_epoch}")
k2.metric("Corridor Health Status", f"{ontrack_count} Green | {delayed_count} Amber | {stalled_count} Red")
k3.metric("Authorized Escrow Release", f"₹{released_cr:.1f} Cr", f"of ₹{total_loan_cr} Cr Facility")
k4.metric("Capital Protected (Holdback)", f"₹{held_cr:.1f} Cr", f"Saves ₹{annual_audit_savings}L/yr audit cost")

st.markdown("<br>", unsafe_allow_html=True)

selected_name = st.session_state.get("seg_select", epoch_df["segment_name"].iloc[0])

# Map status to RGBA colors for WebGL deck.gl layers
rgba_map = {
    "On Track": [16, 185, 129, 230],
    "Delayed": [245, 158, 11, 230],
    "Stalled": [239, 68, 68, 235],
}
map_df = epoch_df.copy()
map_df["color"] = map_df["status"].map(lambda s: rgba_map.get(s, [56, 189, 248, 220]))
map_df["elevation_m"] = map_df["predicted_completion_pct"] * 45.0
map_df["is_selected"] = map_df["segment_name"] == selected_name

corridor_coords = [[float(r["lon"]), float(r["lat"])] for _, r in map_df.iterrows()]
path_data = [{"path": corridor_coords, "name": "Bengaluru STRR (NH-648)"}]
selected_df = map_df[map_df["is_selected"]]

col_map, col_detail = st.columns([1.18, 1.0], gap="large")

with col_map:
    st.markdown("#### 🌍 WebGL 3D Orbital Corridor Twin (Bengaluru STRR)")
    st.caption("Column height = AI Verified Completion % • Color = Escrow Status • Cyan halo = Active Segment")

    corridor_layer = pdk.Layer(
        "PathLayer",
        data=path_data,
        get_path="path",
        get_color=[56, 189, 248, 200],
        width_min_pixels=4,
        pickable=False,
    )

    halo_layer = pdk.Layer(
        "ScatterplotLayer",
        data=selected_df,
        get_position=["lon", "lat"],
        get_fill_color=[56, 189, 248, 65],
        get_line_color=[125, 211, 252, 240],
        line_width_min_pixels=3,
        get_radius=1800,
        stroked=True,
        filled=True,
        pickable=False,
    )

    column_layer = pdk.Layer(
        "ColumnLayer",
        data=map_df,
        get_position=["lon", "lat"],
        get_elevation="elevation_m",
        radius=750,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=13.165,
        longitude=77.760,
        zoom=9.5,
        pitch=38,
        bearing=-12,
    )

    deck = pdk.Deck(
        layers=[corridor_layer, halo_layer, column_layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": "<b>{segment_id} • {segment_name}</b><br/>Status: <b>{status}</b><br/>Completion: <b>{predicted_completion_pct}%</b> (Target: {expected_pct}%)<br/>SAR VV: {sar_vv_db} dB | NDBI: {ndbi}",
            "style": {"backgroundColor": "#0f172a", "color": "#f8fafc", "border": "1px solid #38bdf8"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True)

with col_detail:
    st.markdown("#### 📡 Multi-Sensor Telemetry & Automated Escrow Directive")
    selected_name = st.selectbox("Inspect Corridor Segment:", epoch_df["segment_name"].tolist(), key="seg_select")
    seg_hist = df[df["segment_name"] == selected_name].sort_values("epoch")
    seg_now = epoch_df[epoch_df["segment_name"] == selected_name].iloc[0]

    fig_ts = make_subplots(specs=[[{"secondary_y": True}]])
    fig_ts.add_trace(
        go.Scatter(
            x=seg_hist["epoch"], y=seg_hist["ndbi"],
            name="Sentinel-2 Optical NDBI",
            line=dict(color="#38bdf8", width=3),
            mode="lines+markers",
        ),
        secondary_y=False,
    )
    fig_ts.add_trace(
        go.Scatter(
            x=seg_hist["epoch"], y=seg_hist["sar_vv_db"],
            name="Sentinel-1 SAR Radar VV (dB)",
            line=dict(color="#f97316", width=3, dash="dot"),
            mode="lines+markers",
        ),
        secondary_y=True,
    )
    fig_ts.update_layout(
        height=265,
        paper_bgcolor="rgba(15, 23, 42, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        font=dict(color="#cbd5e1"),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.18),
    )
    fig_ts.update_xaxes(gridcolor="rgba(148,163,184,0.12)")
    fig_ts.update_yaxes(title_text="Optical NDBI", secondary_y=False, gridcolor="rgba(148,163,184,0.12)")
    fig_ts.update_yaxes(title_text="Radar VV (dB)", secondary_y=True, showgrid=False)
    st.plotly_chart(fig_ts, use_container_width=True)

    if seg_now["status"] == "On Track":
        st.success(f"**DIRECTIVE: APPROVE TRANCHE RELEASE** — Verified **{seg_now['predicted_completion_pct']}%** complete (Target: {seg_now['expected_pct']}%).")
    elif seg_now["status"] == "Delayed":
        st.warning(f"**DIRECTIVE: PARTIAL HOLDBACK** — Verified **{seg_now['predicted_completion_pct']}%** vs. {seg_now['expected_pct']}% target ({seg_now['schedule_gap_pct']}% variance).")
    else:
        st.error(f"**DIRECTIVE: FREEZE ESCROW DISBURSEMENT** — Stalled at **{seg_now['predicted_completion_pct']}%** vs. {seg_now['expected_pct']}% target.")

    seg_tranche_cr = round(segment_budget * (seg_now["predicted_completion_pct"] / 100.0), 2)
    st.markdown(f"""
    <div class="audit-card">
        <b>🤖 Automated Orbital Audit Brief ({seg_now['segment_id']} • {selected_epoch}):</b><br>
        • <b>Radar Structural Signal:</b> Sentinel-1 C-band VV backscatter at <b>{seg_now['sar_vv_db']} dB</b> (Δ {seg_now['sar_vv_gain']:+.2f} dB vs. 2022 baseline).<br>
        • <b>Surface Grading Signal:</b> Optical NDBI at <b>{seg_now['ndbi']}</b> and vegetation NDVI at <b>{seg_now['ndvi']}</b>.<br>
        • <b>Escrow Allocation:</b> Release <b>₹{seg_tranche_cr} Cr</b> of ₹{segment_budget:.1f} Cr segment allocation; schedule variance is <b>{seg_now['schedule_gap_pct']:+.1f}%</b>.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📋 Live Escrow Audit Ledger", "📊 Sensor-Fusion Validation Proof"])

with tab1:
    display_cols = ["segment_id", "segment_name", "predicted_completion_pct", "expected_pct", "schedule_gap_pct", "status", "ndvi", "ndbi", "sar_vv_db"]
    st.dataframe(epoch_df[display_cols], use_container_width=True, hide_index=True)

with tab2:
    c_img, c_txt = st.columns([1.15, 1])
    with c_img:
        st.image("validation_chart.png", caption="5-Fold Cross-Validation Error: Sensor Fusion vs. Optical-Only")
    with c_txt:
        st.markdown("""
        ### Why Multi-Sensor Fusion Wins for Aerospace Engineering
        * **All-Weather Monsoon Penetration:** Sentinel-2 optical indices degrade under cloud cover; Sentinel-1 C-band SAR penetrates clouds day and night.
        * **3D Structural Double-Bounce:** Optical bands confuse bare soil with finished flyovers; SAR `VV/VH` backscatter spikes specifically when bridge piers and steel girders rise.
        * **Zero-CapEx Scalability:** Built on open Copernicus satellite archives + OpenStreetMap geometries—deployable across any NHAI highway, port, or airport corridor in India.
        """)