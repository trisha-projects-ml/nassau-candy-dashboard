import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy | Profitability Dashboard",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f1a; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .metric-card {
        background: linear-gradient(135deg, #1e1e3a, #2a2a4a);
        border: 1px solid #3a3a6a;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #a78bfa;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-top: 4px;
    }
    .metric-delta-pos { color: #34d399; font-size: 0.8rem; }
    .metric-delta-neg { color: #f87171; font-size: 0.8rem; }
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #e2e8f0;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #3a3a6a;
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stDateInput"] label { color: #d1d5db !important; }
    .stSidebar { background-color: #13132b; }
    .stSidebar .stMarkdown h2 { color: #a78bfa; }
    .risk-high { color: #f87171; font-weight: 700; }
    .risk-med  { color: #fbbf24; font-weight: 700; }
    .risk-low  { color: #34d399; font-weight: 700; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel("Nassau Candy Distributor.xlsx", sheet_name="Nassau Candy Distributor")
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  errors="coerce")
    df = df[df["Sales"] > 0].copy()
    df = df[df["Units"] > 0].copy()
    df.dropna(subset=["Gross Profit", "Cost", "Sales"], inplace=True)
    df["Gross Margin (%)"]  = (df["Gross Profit"] / df["Sales"]) * 100
    df["Profit per Unit"]   = df["Gross Profit"] / df["Units"]
    df["Revenue per Unit"]  = df["Sales"] / df["Units"]
    df["Cost per Unit"]     = df["Cost"] / df["Units"]
    return df

df_raw = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍬 Nassau Candy")
    st.markdown("### Filters")

    min_date = df_raw["Order Date"].min().date()
    max_date = df_raw["Order Date"].max().date()
    date_range = st.date_input(
        "Order Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    divisions = ["All"] + sorted(df_raw["Division"].dropna().unique().tolist())
    sel_division = st.selectbox("Division", divisions)

    regions = ["All"] + sorted(df_raw["Region"].dropna().unique().tolist())
    sel_region = st.selectbox("Region", regions)

    margin_thresh = st.slider(
        "Min Gross Margin (%)", min_value=0, max_value=100,
        value=0, step=1,
        help="Filter to products with margin above this threshold"
    )

    all_products = sorted(df_raw["Product Name"].dropna().unique().tolist())
    sel_products = st.multiselect("Product Search / Filter", all_products, default=[])

    st.markdown("---")
    st.markdown("**Data:** Nassau Candy Distributor")
    st.markdown(f"**Rows:** {len(df_raw):,}")

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
df = df_raw.copy()

if len(date_range) == 2:
    df = df[(df["Order Date"].dt.date >= date_range[0]) &
            (df["Order Date"].dt.date <= date_range[1])]

if sel_division != "All":
    df = df[df["Division"] == sel_division]

if sel_region != "All":
    df = df[df["Region"] == sel_region]

if margin_thresh > 0:
    df = df[df["Gross Margin (%)"] >= margin_thresh]

if sel_products:
    df = df[df["Product Name"].isin(sel_products)]

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<h1 style='color:#a78bfa; margin-bottom:0;'>🍬 Nassau Candy Distributor</h1>
<p style='color:#9ca3af; font-size:1.05rem; margin-top:4px;'>
    Product Line Profitability & Margin Performance Dashboard
</p>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Product Overview",
    "🏢 Division Performance",
    "🔍 Cost & Margin Diagnostics",
    "📈 Profit Concentration"
])

# ═══════════════════════════════════════════════
# TAB 1 – PRODUCT OVERVIEW
# ═══════════════════════════════════════════════
with tab1:

    # KPI Cards
    total_sales   = df["Sales"].sum()
    total_profit  = df["Gross Profit"].sum()
    avg_margin    = (total_profit / total_sales * 100) if total_sales > 0 else 0
    total_units   = df["Units"].sum()
    ppu           = (total_profit / total_units) if total_units > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>${total_sales/1e6:.2f}M</div>
            <div class='metric-label'>Total Revenue</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>${total_profit/1e3:.1f}K</div>
            <div class='metric-label'>Total Gross Profit</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{avg_margin:.1f}%</div>
            <div class='metric-label'>Avg Gross Margin</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>{total_units:,}</div>
            <div class='metric-label'>Total Units Sold</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>${ppu:.3f}</div>
            <div class='metric-label'>Profit per Unit</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Product Profitability Leaderboard</div>", unsafe_allow_html=True)

    prod_df = df.groupby("Product Name").agg(
        Division=("Division", "first"),
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Total_Cost=("Cost", "sum"),
    ).reset_index()
    prod_df["Gross Margin (%)"]  = (prod_df["Total_Profit"] / prod_df["Total_Sales"] * 100).round(2)
    prod_df["Profit per Unit"]   = (prod_df["Total_Profit"] / prod_df["Total_Units"]).round(4)
    prod_df["Revenue Share (%)"] = (prod_df["Total_Sales"] / prod_df["Total_Sales"].sum() * 100).round(2)
    prod_df["Profit Share (%)"]  = (prod_df["Total_Profit"] / prod_df["Total_Profit"].sum() * 100).round(2)
    prod_df = prod_df.sort_values("Total_Profit", ascending=False)

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.bar(
            prod_df, x="Total_Profit", y="Product Name",
            orientation="h", color="Gross Margin (%)",
            color_continuous_scale="Viridis",
            title="Gross Profit by Product",
            labels={"Total_Profit": "Gross Profit ($)", "Product Name": ""},
            text=prod_df["Gross Margin (%)"].apply(lambda x: f"{x:.1f}%")
        )
        fig.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=420,
            yaxis=dict(categoryorder="total ascending"),
            coloraxis_colorbar=dict(title="Margin %")
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig2 = px.bar(
            prod_df.sort_values("Gross Margin (%)", ascending=False),
            x="Gross Margin (%)", y="Product Name",
            orientation="h", color="Division",
            color_discrete_map={"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"},
            title="Gross Margin % by Product",
            labels={"Product Name": ""}
        )
        fig2.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=420,
            yaxis=dict(categoryorder="total ascending")
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-header'>Profit Contribution Chart</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig3 = px.pie(
            prod_df, values="Total_Profit", names="Product Name",
            title="Profit Share by Product",
            color_discrete_sequence=px.colors.sequential.Plasma_r,
            hole=0.45
        )
        fig3.update_layout(paper_bgcolor="#1e1e3a", font_color="#e2e8f0", height=360)
        fig3.update_traces(textinfo="percent+label")
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        fig4 = px.pie(
            prod_df, values="Total_Sales", names="Division",
            title="Revenue Share by Division",
            color="Division",
            color_discrete_map={"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"},
            hole=0.45
        )
        fig4.update_layout(paper_bgcolor="#1e1e3a", font_color="#e2e8f0", height=360)
        fig4.update_traces(textinfo="percent+label")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<div class='section-header'>Detailed Product Table</div>", unsafe_allow_html=True)
    display_df = prod_df.rename(columns={
        "Product Name": "Product", "Total_Sales": "Revenue ($)",
        "Total_Profit": "Gross Profit ($)", "Total_Units": "Units",
        "Total_Cost": "Cost ($)"
    })[["Product", "Division", "Revenue ($)", "Gross Profit ($)", "Units",
        "Cost ($)", "Gross Margin (%)", "Profit per Unit",
        "Revenue Share (%)", "Profit Share (%)"]].copy()

    for col in ["Revenue ($)", "Gross Profit ($)", "Cost ($)"]:
        display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")
    display_df["Profit per Unit"] = display_df["Profit per Unit"].apply(lambda x: f"${x:.4f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════
# TAB 2 – DIVISION PERFORMANCE
# ═══════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-header'>Division-Level Performance Summary</div>", unsafe_allow_html=True)

    div_df = df.groupby("Division").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Cost=("Cost", "sum"),
        Total_Units=("Units", "sum"),
        Num_Products=("Product Name", "nunique"),
        Num_Orders=("Order ID", "nunique"),
    ).reset_index()
    div_df["Gross Margin (%)"]  = (div_df["Total_Profit"] / div_df["Total_Sales"] * 100).round(2)
    div_df["Profit per Unit"]   = (div_df["Total_Profit"] / div_df["Total_Units"]).round(4)
    div_df["Revenue Share (%)"] = (div_df["Total_Sales"] / div_df["Total_Sales"].sum() * 100).round(2)
    div_df["Profit Share (%)"]  = (div_df["Total_Profit"] / div_df["Total_Profit"].sum() * 100).round(2)

    # KPI per division
    cols = st.columns(len(div_df))
    for i, row in div_df.iterrows():
        with cols[list(div_df.index).index(i)]:
            color_map = {"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"}
            c = color_map.get(row["Division"], "#a78bfa")
            st.markdown(f"""<div class='metric-card' style='border-color:{c}40;'>
                <div style='color:{c}; font-size:1.1rem; font-weight:700;'>{row["Division"]}</div>
                <div class='metric-value' style='color:{c};'>{row["Gross Margin (%)"]:.1f}%</div>
                <div class='metric-label'>Avg Margin</div>
                <div style='color:#9ca3af; font-size:0.8rem; margin-top:6px;'>
                    Rev: ${row["Total_Sales"]/1e3:.0f}K &nbsp;|&nbsp; Profit: ${row["Total_Profit"]/1e3:.1f}K
                </div>
            </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Revenue", x=div_df["Division"],
            y=div_df["Total_Sales"],
            marker_color=["#a78bfa", "#34d399", "#fb923c"][:len(div_df)]
        ))
        fig.add_trace(go.Bar(
            name="Gross Profit", x=div_df["Division"],
            y=div_df["Total_Profit"],
            marker_color=["#7c3aed", "#059669", "#c2410c"][:len(div_df)]
        ))
        fig.update_layout(
            barmode="group", title="Revenue vs Gross Profit by Division",
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=380,
            legend=dict(bgcolor="#1e1e3a")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            div_df, x="Division", y="Gross Margin (%)",
            color="Division", text="Gross Margin (%)",
            color_discrete_map={"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"},
            title="Gross Margin % by Division"
        )
        fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig2.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=380, showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='section-header'>Margin Distribution by Division</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.box(
            df, x="Division", y="Gross Margin (%)",
            color="Division",
            color_discrete_map={"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"},
            title="Gross Margin Distribution per Division",
            points="outliers"
        )
        fig3.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=380, showlegend=False
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.bar(
            div_df, x="Division", y=["Revenue Share (%)", "Profit Share (%)"],
            barmode="group",
            color_discrete_sequence=["#a78bfa", "#34d399"],
            title="Revenue Share vs Profit Share by Division"
        )
        fig4.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=380,
            legend=dict(bgcolor="#1e1e3a")
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<div class='section-header'>Monthly Profit Trend by Division</div>", unsafe_allow_html=True)
    monthly = df.copy()
    monthly["Month"] = monthly["Order Date"].dt.to_period("M").astype(str)
    monthly_div = monthly.groupby(["Month", "Division"])["Gross Profit"].sum().reset_index()
    fig5 = px.line(
        monthly_div, x="Month", y="Gross Profit", color="Division",
        color_discrete_map={"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"},
        title="Monthly Gross Profit Trend by Division",
        markers=True
    )
    fig5.update_layout(
        plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
        font_color="#e2e8f0", height=380,
        xaxis_tickangle=-45, legend=dict(bgcolor="#1e1e3a")
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("<div class='section-header'>Division Summary Table</div>", unsafe_allow_html=True)
    disp_div = div_df.copy()
    for col in ["Total_Sales", "Total_Profit", "Total_Cost"]:
        disp_div[col] = disp_div[col].apply(lambda x: f"${x:,.2f}")
    disp_div["Profit per Unit"] = disp_div["Profit per Unit"].apply(lambda x: f"${x:.4f}")
    disp_div.columns = ["Division", "Revenue ($)", "Gross Profit ($)", "Cost ($)",
                        "Units", "Products", "Orders", "Gross Margin (%)",
                        "Profit per Unit", "Revenue Share (%)", "Profit Share (%)"]
    st.dataframe(disp_div, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════
# TAB 3 – COST & MARGIN DIAGNOSTICS
# ═══════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Cost vs Sales Scatter Analysis</div>", unsafe_allow_html=True)

    prod_scatter = df.groupby(["Product Name", "Division"]).agg(
        Total_Sales=("Sales", "sum"),
        Total_Cost=("Cost", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
    ).reset_index()
    prod_scatter["Gross Margin (%)"] = (prod_scatter["Total_Profit"] / prod_scatter["Total_Sales"] * 100).round(2)
    prod_scatter["Profit per Unit"]  = (prod_scatter["Total_Profit"] / prod_scatter["Total_Units"]).round(4)
    prod_scatter["Cost Ratio (%)"]   = (prod_scatter["Total_Cost"] / prod_scatter["Total_Sales"] * 100).round(2)

    fig = px.scatter(
        prod_scatter, x="Total_Cost", y="Total_Sales",
        size="Total_Profit", color="Gross Margin (%)",
        hover_name="Product Name",
        hover_data={"Division": True, "Gross Margin (%)": ":.2f",
                    "Cost Ratio (%)": ":.2f", "Total_Profit": ":,.2f"},
        color_continuous_scale="RdYlGn",
        size_max=60,
        title="Cost vs Sales (bubble size = Gross Profit, color = Margin %)"
    )
    # Add diagonal reference line (break-even)
    max_val = max(prod_scatter["Total_Sales"].max(), prod_scatter["Total_Cost"].max())
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines", line=dict(dash="dash", color="#6b7280", width=1),
        name="Break-even", showlegend=True
    ))
    fig.update_layout(
        plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
        font_color="#e2e8f0", height=480
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-header'>Cost Ratio by Product</div>", unsafe_allow_html=True)
        prod_cost = prod_scatter.sort_values("Cost Ratio (%)", ascending=False)
        fig2 = px.bar(
            prod_cost, x="Cost Ratio (%)", y="Product Name",
            orientation="h", color="Cost Ratio (%)",
            color_continuous_scale="RdYlGn_r",
            title="Cost as % of Revenue (lower = better)",
            text=prod_cost["Cost Ratio (%)"].apply(lambda x: f"{x:.1f}%")
        )
        fig2.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=420,
            yaxis=dict(categoryorder="total ascending")
        )
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("<div class='section-header'>Profit per Unit by Product</div>", unsafe_allow_html=True)
        prod_ppu = prod_scatter.sort_values("Profit per Unit", ascending=False)
        fig3 = px.bar(
            prod_ppu, x="Profit per Unit", y="Product Name",
            orientation="h", color="Division",
            color_discrete_map={"Chocolate": "#a78bfa", "Sugar": "#34d399", "Other": "#fb923c"},
            title="Profit per Unit by Product",
            text=prod_ppu["Profit per Unit"].apply(lambda x: f"${x:.4f}")
        )
        fig3.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=420,
            yaxis=dict(categoryorder="total ascending")
        )
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<div class='section-header'>⚠️ Margin Risk Flags</div>", unsafe_allow_html=True)

    avg_margin_overall = prod_scatter["Gross Margin (%)"].mean()
    low_margin_thresh  = avg_margin_overall * 0.75

    prod_scatter["Risk Flag"] = prod_scatter["Gross Margin (%)"].apply(
        lambda m: "🔴 HIGH RISK" if m < low_margin_thresh
        else ("🟡 MEDIUM RISK" if m < avg_margin_overall else "🟢 HEALTHY")
    )
    prod_scatter["Action"] = prod_scatter.apply(lambda row:
        "Discontinuation / Cost Renegotiation Review"
        if row["Gross Margin (%)"] < low_margin_thresh
        else ("Repricing Recommended"
              if row["Gross Margin (%)"] < avg_margin_overall
              else "Maintain / Promote"),
        axis=1
    )

    risk_display = prod_scatter[[
        "Product Name", "Division", "Gross Margin (%)",
        "Cost Ratio (%)", "Profit per Unit", "Risk Flag", "Action"
    ]].sort_values("Gross Margin (%)")
    risk_display["Gross Margin (%)"] = risk_display["Gross Margin (%)"].apply(lambda x: f"{x:.2f}%")
    risk_display["Cost Ratio (%)"]   = risk_display["Cost Ratio (%)"].apply(lambda x: f"{x:.2f}%")
    risk_display["Profit per Unit"]  = risk_display["Profit per Unit"].apply(lambda x: f"${x:.4f}")

    st.dataframe(risk_display, use_container_width=True, hide_index=True)

    # Summary flags
    total_prods = len(prod_scatter)
    high_risk = (prod_scatter["Risk Flag"] == "🔴 HIGH RISK").sum()
    med_risk  = (prod_scatter["Risk Flag"] == "🟡 MEDIUM RISK").sum()
    healthy   = (prod_scatter["Risk Flag"] == "🟢 HEALTHY").sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 High Risk Products",   high_risk, f"out of {total_prods}")
    c2.metric("🟡 Medium Risk Products", med_risk,  f"out of {total_prods}")
    c3.metric("🟢 Healthy Products",     healthy,   f"out of {total_prods}")


# ═══════════════════════════════════════════════
# TAB 4 – PROFIT CONCENTRATION (PARETO)
# ═══════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Pareto Analysis — Profit & Revenue Concentration</div>", unsafe_allow_html=True)

    pareto_df = df.groupby("Product Name").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Division=("Division", "first")
    ).reset_index().sort_values("Total_Profit", ascending=False)

    pareto_df["Cumulative Profit (%)"]  = (pareto_df["Total_Profit"].cumsum()  / pareto_df["Total_Profit"].sum()  * 100)
    pareto_df["Cumulative Revenue (%)"] = (pareto_df["Total_Sales"].cumsum()   / pareto_df["Total_Sales"].sum()   * 100)
    pareto_df["Product Rank"]           = range(1, len(pareto_df) + 1)
    pareto_df["Product %"]              = (pareto_df["Product Rank"] / len(pareto_df) * 100)

    col1, col2 = st.columns(2)

    with col1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=pareto_df["Product Name"], y=pareto_df["Total_Profit"],
            name="Gross Profit", marker_color="#a78bfa"
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=pareto_df["Product Name"], y=pareto_df["Cumulative Profit (%)"],
            name="Cumulative %", line=dict(color="#f59e0b", width=2),
            mode="lines+markers"
        ), secondary_y=True)
        fig.add_hline(y=80, line_dash="dash", line_color="#f87171",
                      annotation_text="80% Threshold", secondary_y=True)
        fig.update_layout(
            title="Pareto Chart – Gross Profit",
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=420,
            xaxis_tickangle=-45, legend=dict(bgcolor="#1e1e3a")
        )
        fig.update_yaxes(title_text="Gross Profit ($)", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        pareto_rev = df.groupby("Product Name").agg(
            Total_Sales=("Sales", "sum")
        ).reset_index().sort_values("Total_Sales", ascending=False)
        pareto_rev["Cumulative Revenue (%)"] = (pareto_rev["Total_Sales"].cumsum() / pareto_rev["Total_Sales"].sum() * 100)
        fig2.add_trace(go.Bar(
            x=pareto_rev["Product Name"], y=pareto_rev["Total_Sales"],
            name="Revenue", marker_color="#34d399"
        ), secondary_y=False)
        fig2.add_trace(go.Scatter(
            x=pareto_rev["Product Name"], y=pareto_rev["Cumulative Revenue (%)"],
            name="Cumulative %", line=dict(color="#f59e0b", width=2),
            mode="lines+markers"
        ), secondary_y=True)
        fig2.add_hline(y=80, line_dash="dash", line_color="#f87171",
                       annotation_text="80% Threshold", secondary_y=True)
        fig2.update_layout(
            title="Pareto Chart – Revenue",
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=420,
            xaxis_tickangle=-45, legend=dict(bgcolor="#1e1e3a")
        )
        fig2.update_yaxes(title_text="Revenue ($)", secondary_y=False)
        fig2.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 105])
        st.plotly_chart(fig2, use_container_width=True)

    # 80/20 summary
    st.markdown("<div class='section-header'>80/20 Dependency Summary</div>", unsafe_allow_html=True)

    prods_for_80_profit  = (pareto_df["Cumulative Profit (%)"]  <= 80).sum() + 1
    prods_for_80_revenue = (pareto_rev["Cumulative Revenue (%)"] <= 80).sum() + 1
    total_p = len(pareto_df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products → 80% of Profit",  prods_for_80_profit,  f"{prods_for_80_profit/total_p*100:.0f}% of portfolio")
    c2.metric("Products → 80% of Revenue", prods_for_80_revenue, f"{prods_for_80_revenue/total_p*100:.0f}% of portfolio")
    c3.metric("Total Products", total_p)
    c4.metric("Concentration Risk", "HIGH" if prods_for_80_profit <= total_p * 0.3 else "MODERATE")

    st.markdown("<div class='section-header'>Region-Level Profit Concentration</div>", unsafe_allow_html=True)

    region_df = df.groupby("Region").agg(
        Total_Sales=("Sales", "sum"),
        Total_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
    ).reset_index()
    region_df["Gross Margin (%)"] = (region_df["Total_Profit"] / region_df["Total_Sales"] * 100).round(2)
    region_df["Profit Share (%)"] = (region_df["Total_Profit"] / region_df["Total_Profit"].sum() * 100).round(2)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.bar(
            region_df.sort_values("Total_Profit", ascending=False),
            x="Region", y="Total_Profit",
            color="Gross Margin (%)", color_continuous_scale="Viridis",
            text=region_df.sort_values("Total_Profit", ascending=False)["Profit Share (%)"].apply(lambda x: f"{x:.1f}%"),
            title="Profit by Region"
        )
        fig3.update_layout(
            plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
            font_color="#e2e8f0", height=360
        )
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.pie(
            region_df, values="Total_Profit", names="Region",
            title="Profit Concentration by Region",
            color_discrete_sequence=["#a78bfa", "#34d399", "#fb923c", "#38bdf8"],
            hole=0.4
        )
        fig4.update_layout(paper_bgcolor="#1e1e3a", font_color="#e2e8f0", height=360)
        fig4.update_traces(textinfo="percent+label")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("<div class='section-header'>Product × Division Profit Heatmap</div>", unsafe_allow_html=True)
    heat_df = df.groupby(["Product Name", "Division"])["Gross Profit"].sum().reset_index()
    heat_pivot = heat_df.pivot(index="Product Name", columns="Division", values="Gross Profit").fillna(0)
    fig5 = px.imshow(
        heat_pivot, color_continuous_scale="Viridis",
        title="Gross Profit Heatmap — Product × Division",
        aspect="auto"
    )
    fig5.update_layout(
        plot_bgcolor="#1e1e3a", paper_bgcolor="#1e1e3a",
        font_color="#e2e8f0", height=500
    )
    st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<hr style='border-color:#3a3a6a; margin-top:2rem;'/>
<p style='text-align:center; color:#4b5563; font-size:0.8rem;'>
    Nassau Candy Distributor | Product Line Profitability Dashboard
</p>
""", unsafe_allow_html=True)
