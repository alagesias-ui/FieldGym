# IMPORT LIBRARIES
import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import psycopg2
import plotly.express as px

st.set_page_config(
    page_title="FieldGym | Datová platforma",
    page_icon="https://www.fieldgym.cz/files/favicon/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CONNECT TO DATABASE
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌CHYBA: Chybí DATABASE_URL v .env souboru!")
    exit()

engine_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1).replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(engine_url)

try:
    with engine.connect() as conn:
        print("✅Úspěšně připojeno k Neon.tech databázi přes SQLAlchemy!")
except Exception as e:
    print(f"❌Chyba při připojení k DB: {e}")
    exit()

# DATAFRAMES
## MAIN DATAFRAME
try:
    query = "SELECT * FROM fct_fieldgym_data"
    df = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno {len(df)} řádků z data  báze!")
except Exception as e: 
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

## TREND DATAFRAME
try:
    query = "SELECT * FROM fct_weeks"
    df_trend = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno {len(df_trend)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

## TIME/DATE DATAFRAME
try:
    query = "SELECT DISTINCT * FROM fct_wdays_time"
    df_wdays = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno {len(df_wdays)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

## FAVORITE ACTIVITIES DATAFRAME
try:
    query = "SELECT DISTINCT activity_type, total_visits FROM fct_favorite_activity_month"
    df_activities = pd.read_sql(query, con=engine)
    list_activities = ["Vše"] + df_activities['activity_type'].unique().dropna().tolist()
    print(f"✅Úspěšně načteno {len(df_activities)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    list_activities = ["Vše"]
    exit()

## FAVORITE TARIFFS DATAFRAME
try:
    query = "SELECT DISTINCT tariff_type, count FROM fct_favorite_tariffs"
    df_tariffs = pd.read_sql(query, con=engine)
    list_tariffs = ["Vše"] + df_tariffs['tariff_type'].unique().dropna().tolist()
    print(f"✅Úspěšně načteno {len(df_tariffs)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    list_tariffs = ["Vše"]
    exit()

## DATES DATAFRAME
try:
    query = "SELECT MIN(date_only) AS min_date, MAX(date_only) AS max_date FROM fct_fieldgym_data"
    df_dates = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno rozsah dat z databáze!")
    min_date = df_dates["min_date"].iloc[0]
    max_date = df_dates["max_date"].iloc[0]
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

## CHURN DATAFRAME
try:
    query = "SELECT member_id, total_visits, first_visit, last_visit, days_since_last_visit FROM fct_churn"
    df_churn = pd.read_sql(query, con=engine)
    for date_col in ["first_visit", "last_visit"]:
        if date_col in df_churn.columns:
            df_churn[date_col] = pd.to_datetime(df_churn[date_col]).dt.strftime("%d.%m.%Y")
    df_churn.rename(columns={'member_id': 'ID člena', 'total_visits': 'Počet návštěv', 'days_since_last_visit': 'Dny od poslední návštěvy','first_visit':'První návštěva','last_visit':'Poslední návštěva'}, inplace=True)
    print(f"✅Úspěšně načteno {len(df_churn)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

# KPIs
## Návštěvnost
visitors_last_30_days = df[df['date_only'] >= (max(df['date_only']) - pd.Timedelta(days=30))]['member_id'].nunique()
visitors_last_60_30_days = df[(df['date_only'] >= (max(df['date_only']) - pd.Timedelta(days=60))) & (df['date_only'] < (max(df['date_only']) - pd.Timedelta(days=30)))]['member_id'].nunique()
visitors_delta_pct = ((visitors_last_30_days - visitors_last_60_30_days) / visitors_last_60_30_days) * 100 if visitors_last_60_30_days != 0 else 0

## Včerejší návštěvnost
visitors_yesterday = df[df['date_only'] == (max(df['date_only']) - pd.Timedelta(days=1))]['member_id'].nunique()
average_daily_visitors = df.groupby('date_only')['member_id'].nunique().mean()
visitors_yesterday_delta_pct = ((visitors_yesterday - average_daily_visitors) / average_daily_visitors) * 100 if average_daily_visitors != 0 else 0

## Aktuálně aktivní členové
members_active_currently = df['member_id'].nunique()
members_active_last_month = df[df['date_only'] >= (max(df['date_only']) - pd.Timedelta(days=30))]['member_id'].nunique()
members_delta_pct = ((members_active_currently - members_active_last_month) / members_active_last_month) * 100 if members_active_last_month != 0 else 0

# CHARTS
# Official FieldGym.cz palette:
# --main-color-01: #27A6B0 (Turquoise)
# --main-color-02: #B3ECEE (Aqua Ice)
# --main-color-03: #12323A (Deep Petrol)
# Body text: #234C56, Light tint: #EFFCFC
CHART_FONT = dict(family="Inter, system-ui, -apple-system, sans-serif", size=13, color="#12323A")

# Distinct categorical palette anchored in FieldGym's brand colors (#12323A, #27A6B0)
# paired with high-contrast complementary hues so pie slices are immediately distinguishable
DISTINCT_CHART_PALETTE = [
    "#27A6B0",  # FieldGym Primary Turquoise (--main-color-01)
    "#12323A",  # FieldGym Deep Petrol (--main-color-03)
    "#F59E0B",  # Warm Amber Gold
    "#E05A47",  # Terracotta Coral
    "#4F46E5",  # Royal Indigo
    "#10B981",  # Vibrant Emerald
    "#8B5CF6",  # Vivid Violet
    "#7FDDE1",  # FieldGym Bright Cyan
]
DAYS_ORDER_TOP_DOWN = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]

if "den_v_tydnu" in df_wdays.columns and df_wdays["den_v_tydnu"].dtype == object:
    df_wdays["den_v_tydnu"] = df_wdays["den_v_tydnu"].str.strip()

## Aktuální trend návštěvnosti - line chart
df_trend['week_start'] = pd.to_datetime(df_trend['week_start'])
current_trend_chart = px.line(
    df_trend,
    x='week_start',
    y='number_of_unique_visitors',
    custom_data=['week'],
    labels={'week_start': 'Týden', 'number_of_unique_visitors': 'Počet návštěvníků'},
    template="plotly_white",
)
current_trend_chart.update_traces(
    line=dict(color="#27A6B0", width=3),
    mode="lines+markers",
    marker=dict(size=6, color="#12323A", line=dict(color="#FFFFFF", width=1.5)),
    fill="tozeroy",
    fillcolor="rgba(39, 166, 176, 0.12)",
    hovertemplate="<b>Týden:</b> %{customdata[0]}<br><b>Začátek týdne:</b> %{x|%d.%m.%Y}<br><b>Počet návštěvníků:</b> %{y:,}<extra></extra>",
)
current_trend_chart.update_layout(
    font=CHART_FONT,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=10, r=10, t=20, b=10),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#12323A", font_size=13, font_color="#FFFFFF"),
    xaxis=dict(
        title=dict(text="Datum", font=dict(color="#12323A", size=13)),
        tickfont=dict(color="#234C56", size=12),
        tickformat="%m.%Y",
        hoverformat="%d.%m.%Y",
        showgrid=False,
        linecolor="#B3ECEE",
    ),
    yaxis=dict(
        title=dict(text="Počet návštěv", font=dict(color="#12323A", size=13)),
        tickfont=dict(color="#234C56", size=12),
        gridcolor="#EFFCFC",
        zeroline=False,
    ),
)

## Vytíženost v čase - heatmap
occupancy_chart = px.density_heatmap(
    df_wdays,
    x='hour',
    y='den_v_tydnu',
    z='member_id',
    histfunc='count',
    category_orders={'den_v_tydnu': DAYS_ORDER_TOP_DOWN},
    color_continuous_scale=['#EFFCFC', '#B3ECEE', '#27A6B0', '#234C56', '#12323A'],
    labels={'hour': 'Hodina', 'den_v_tydnu': 'Den v týdnu', 'member_id': 'Počet návštěv'},
    template="plotly_white",
)
occupancy_chart.update_traces(
    xgap=2,
    ygap=2,
    hovertemplate="<b>Den:</b> %{y}<br><b>Hodina:</b> %{x}:00<br><b>Návštěvy:</b> %{z:,}<extra></extra>",
)
occupancy_chart.update_layout(
    font=CHART_FONT,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(l=10, r=10, t=20, b=10),
    hoverlabel=dict(bgcolor="#12323A", font_size=13, font_color="#FFFFFF"),
    xaxis=dict(
        title=dict(text="Hodina", font=dict(color="#12323A", size=13)),
        tickfont=dict(color="#234C56", size=12),
    ),
    yaxis=dict(
        title=dict(text="Den v týdnu", font=dict(color="#12323A", size=13)),
        tickfont=dict(color="#234C56", size=12),
        categoryorder="array",
        categoryarray=list(reversed(DAYS_ORDER_TOP_DOWN)),
    ),
    coloraxis_colorbar=dict(
        title=dict(text="Návštěvy", font=dict(color="#12323A", size=13)),
        tickfont=dict(color="#234C56", size=12),
    ),
)

## Podíl tarifů a aktivit - pie charts
pie_chart_tariffs = px.pie(
    df_tariffs,
    names='tariff_type',
    values='count',
    title='Podíl tarifů mezi členy',
    hole=0.45,
    color_discrete_sequence=DISTINCT_CHART_PALETTE,
    template="plotly_white",
)
pie_chart_tariffs.update_traces(
    textinfo="percent",
    textfont=dict(size=13, color="#FFFFFF"),
    marker=dict(line=dict(color="#FFFFFF", width=2.5)),
    hovertemplate="<b>%{label}</b><br>Počet: %{value:,} (%{percent})<extra></extra>",
)
pie_chart_tariffs.update_layout(
    font=CHART_FONT,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    title=dict(text="Podíl tarifů mezi členy", font=dict(family="Oswald, sans-serif", size=18, color="#12323A")),
    margin=dict(l=20, r=20, t=55, b=85),
    hoverlabel=dict(bgcolor="#12323A", font_size=13, font_color="#FFFFFF"),
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.08,
        xanchor="center",
        x=0.5,
        font=dict(color="#12323A", size=13),
        bgcolor="rgba(255, 255, 255, 0.95)",
    ),
)

pie_chart_activities = px.pie(
    df_activities,
    names='activity_type',
    values='total_visits',
    title='Podíl aktivit mezi členy',
    hole=0.45,
    color_discrete_sequence=DISTINCT_CHART_PALETTE,
    template="plotly_white",
)
pie_chart_activities.update_traces(
    textinfo="percent",
    textfont=dict(size=13, color="#FFFFFF"),
    marker=dict(line=dict(color="#FFFFFF", width=2.5)),
    hovertemplate="<b>%{label}</b><br>Počet návštěv: %{value:,} (%{percent})<extra></extra>",
)
pie_chart_activities.update_layout(
    font=CHART_FONT,
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    title=dict(text="Podíl aktivit mezi členy", font=dict(family="Oswald, sans-serif", size=18, color="#12323A")),
    margin=dict(l=20, r=20, t=55, b=85),
    hoverlabel=dict(bgcolor="#12323A", font_size=13, font_color="#FFFFFF"),
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.08,
        xanchor="center",
        x=0.5,
        font=dict(color="#12323A", size=13),
        bgcolor="rgba(255, 255, 255, 0.95)",
    ),
)

# OFFICIAL FIELDGYM.CZ SVG LOGO
FIELDGYM_LOGO_SVG = (
    '<div class="fg-logo-wrap">'
    '<svg class="fg-logo-mark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 60">'
    '<path d="M0,17.1V0h44v8.7h-22c-10.9,0-16.3,1.3-22,8.4Z"/>'
    '<path d="M44,23.4v-8.7h-22C9.4,14.8,0,24.9,0,36.3v3.9h8.8v-4.4c.3-6.9,6.1-12.4,13.2-12.4,0,0,22,0,22,0Z"/>'
    '<path d="M22,60h1.3c11.9-.7,20.7-10.4,20.7-21.6v-8.7h-22v8.7h13.2c0,7.2-5.9,13-13.2,13v8.6Z"/>'
    '</svg>'
    '<svg class="fg-logo-wordmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 124 60">'
    '<path d="M14.7,22.1h4v16h-4s0-16,0-16Z"/><path d="M35.3,22.1h4v12.4h7.3v3.6h-11.3v-16Z"/>'
    '<path d="M49.7,38.1v-16h6.1c2.4,0,4.3.7,5.7,2.2,1.4,1.4,2.1,3.4,2.1,5.8s-.7,4.4-2.1,5.8c-1.4,1.4-3.3,2.2-5.7,2.2h-6.1ZM53.7,34.6h3c.3,0,.7-.2,1-.4.4-.2.7-.5.9-.8s.4-.8.6-1.3.2-1.2.2-1.9,0-1.4-.2-1.9-.4-1-.6-1.3-.5-.6-.9-.8c-.4-.2-.7-.3-1-.4h-3v8.9h0Z"/>'
    '<path d="M11.7,22.1H0v16h4v-6h4v-3.3h-4v-3.2h7.6v-3.6h0Z"/><path d="M21.7,22.1v3.5h10.6v-3.5h-10.6Z"/><path d="M21.7,28.5v3.3h7.1v-3.3h-7.1Z"/><path d="M21.7,34.6v3.5h10.6v-3.5h-10.6Z"/>'
    '<path d="M82.5,29.4h6.7v8.3h-3v-1.5c-1.1,1.2-2.6,1.9-4.6,1.9s-2-.2-2.8-.5c-.9-.4-1.6-.9-2.3-1.5-.7-.7-1.2-1.5-1.5-2.5-.4-1-.6-2.1-.6-3.3s.3-3,.9-4.2c.6-1.2,1.5-2.2,2.7-2.9,1.1-.7,2.5-1,4-1s3.4.5,4.7,1.4c1.3,1,2,2.3,2.3,3.9h-3.9c-.2-.6-.6-1.1-1.1-1.5-.6-.3-1.2-.5-1.9-.5s-.9,0-1.4.3c-.4.2-.8.4-1.2.8s-.7.9-.9,1.5-.3,1.3-.3,2.2c0,1.5.3,2.6,1,3.5.7.8,1.6,1.2,2.8,1.2s1.6-.2,2.2-.6c.6-.4,1.1-1,1.4-1.8h-3.1v-3h0v-.2h0Z"/>'
    '<path d="M110.8,27.5v10.5h-3.8v-15.3h5.3l3.2,10.9,3.2-10.9h5.3v15.3h-3.8v-10.5l-3,10.5h-3.4l-3-10.5h0Z"/>'
    '<path d="M104.5,22.7h-4.2l-3.1,6-3.1-5.8v-.3h-4s.2.4.4.7l5,8.9-2.9,5.7h4.2l7.8-15.3h-.1Z"/>'
    '</svg>'
    '</div>'
)

# FORMATTING (Official fieldgym.cz theme: #27A6B0, #B3ECEE, #12323A, #234C56, #EFFCFC)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Oswald:wght@500;600;700&display=swap');

    :root {
        --main-color-01: #27A6B0;
        --main-color-02: #B3ECEE;
        --main-color-03: #12323A;
        --body-text: #234C56;
        --surface-tint: #EFFCFC;
    }

    html, body, .stApp {
        background-color: #FFFFFF !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: #234C56;
    }

    /* Top header bar */
    header[data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1280px !important;
    }

    /* FieldGym SVG Logo styling */
    .fg-logo-wrap {
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .fg-logo-mark {
        height: 44px;
        width: auto;
        fill: #27A6B0;
    }
    .fg-logo-wordmark {
        height: 44px;
        width: auto;
        fill: #12323A;
    }

    /* Hero header with logo */
    .fg-hero-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.75rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #12323A 0%, #234C56 100%);
        border-radius: 14px;
        border-bottom: 4px solid #27A6B0;
        box-shadow: 0 4px 14px rgba(18, 50, 58, 0.12);
    }
    .fg-hero-left {
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }
    .fg-hero-header .fg-logo-mark {
        height: 52px;
        fill: #B3ECEE;
    }
    .fg-hero-header .fg-logo-wordmark {
        height: 52px;
        fill: #FFFFFF;
    }
    .fg-hero-divider {
        width: 2px;
        height: 42px;
        background-color: #27A6B0;
        opacity: 0.7;
    }
    .fg-hero-title {
        font-family: 'Oswald', sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        margin: 0 !important;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .fg-hero-subtitle {
        color: #B3ECEE !important;
        font-size: 0.9rem !important;
        margin: 0.15rem 0 0 0 !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 2px solid #B3ECEE !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #12323A !important;
    }

    /* Sidebar Filters (Selectbox, Dropdowns, Sliders) */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #EFFCFC !important;
        border: 1px solid #27A6B0 !important;
        border-radius: 8px !important;
        color: #12323A !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #12323A !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] svg {
        fill: #27A6B0 !important;
    }

    /* Dropdown popover menu */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    ul[role="listbox"] {
        background-color: #FFFFFF !important;
        border: 1px solid #27A6B0 !important;
        border-radius: 8px !important;
    }
    li[role="option"] {
        background-color: #FFFFFF !important;
        color: #12323A !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #EFFCFC !important;
        color: #27A6B0 !important;
        font-weight: 600 !important;
    }

    /* Sidebar navigation links */
    .sidebar-nav {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        margin-top: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .sidebar-nav a {
        text-decoration: none !important;
        color: #234C56 !important;
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        font-size: 0.92rem;
        font-weight: 500;
        transition: all 0.15s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-left: 3px solid transparent;
    }
    .sidebar-nav a:hover {
        background-color: #EFFCFC;
        color: #27A6B0 !important;
        border-left: 3px solid #27A6B0;
    }

    /* Headings & text (Oswald font like fieldgym.cz) */
    h1, h2, h3 {
        font-family: 'Oswald', sans-serif !important;
        color: #27A6B0 !important;
        letter-spacing: 0.01em;
    }

    .section-desc {
        color: #234C56 !important;
        font-size: 0.95rem;
        line-height: 1.55;
        margin-top: -0.25rem;
        margin-bottom: 1rem;
        background-color: #EFFCFC;
        border-left: 4px solid #27A6B0;
        padding: 0.7rem 1rem;
        border-radius: 0 8px 8px 0;
    }

    .chart-caption {
        color: #234C56 !important;
        font-size: 0.88rem;
        line-height: 1.45;
        margin-top: 0.35rem;
        margin-bottom: 0.25rem;
        padding: 0.45rem 0.75rem;
        background-color: #F8FAFC;
        border-radius: 6px;
        border: 1px solid #E2E8F0;
    }

    /* KPI Metric Cards */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #B3ECEE;
        border-top: 4px solid #27A6B0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem !important;
        box-shadow: 0 2px 8px rgba(18, 50, 58, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(39, 166, 176, 0.14);
    }

    [data-testid="stMetricLabel"] p {
        color: #234C56 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
    }

    [data-testid="stMetricValue"] div {
        font-family: 'Oswald', sans-serif !important;
        color: #12323A !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
    }

    /* High-contrast KPI Delta badge (Positive = Green, Negative = Red) */
    [data-testid="stMetricDelta"] {
        padding: 5px 12px !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        width: fit-content !important;
        background-color: #EFFCFC !important;
        color: #12323A !important;
        border: 1px solid #B3ECEE !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        margin-top: 0.45rem !important;
    }

    /* Positive delta (up arrow) -> Deep emerald green on soft mint badge */
    [data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Up"], svg path[d*="M4"], svg path[d*="m4"]) {
        background-color: #D1FAE5 !important;
        color: #065F46 !important;
        border: 1px solid #6EE7B7 !important;
    }

    /* Negative delta (down arrow) -> Deep crimson red on soft rose badge */
    [data-testid="stMetricDelta"]:has([data-testid="stMetricDeltaIcon-Down"], svg path[d*="M20"], svg path[d*="m20"]) {
        background-color: #FEE2E2 !important;
        color: #991B1B !important;
        border: 1px solid #FCA5A5 !important;
    }

    [data-testid="stMetricDelta"] div,
    [data-testid="stMetricDelta"] span {
        color: inherit !important;
    }

    [data-testid="stMetricDelta"] svg {
        fill: currentColor !important;
        color: inherit !important;
    }

    /* Styled Churn Table */
    .churn-table-wrapper {
        max-height: 440px;
        overflow-y: auto;
        border: 1px solid #B3ECEE;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(18, 50, 58, 0.05);
    }
    .churn-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.92rem;
        background-color: #FFFFFF;
        color: #234C56;
    }
    .churn-table thead th {
        position: sticky;
        top: 0;
        font-family: 'Oswald', sans-serif;
        letter-spacing: 0.03em;
        background-color: #12323A;
        color: #B3ECEE !important;
        font-weight: 600;
        text-align: center;
        padding: 0.85rem 1rem;
        border-bottom: 2px solid #27A6B0;
        z-index: 1;
    }
    .churn-table tbody tr {
        border-bottom: 1px solid #E2E8F0;
        transition: background-color 0.12s ease;
    }
    .churn-table tbody tr:nth-child(even) {
        background-color: #F8FAFC;
    }
    .churn-table tbody tr:hover {
        background-color: #EFFCFC;
    }
    .churn-table td {
        padding: 0.75rem 1rem;
        text-align: center;
        color: #12323A;
    }
    .churn-badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.82rem;
        background-color: #EFFCFC;
        color: #12323A;
        border: 1px solid #27A6B0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# SIDEBAR
with st.sidebar:
    st.markdown(FIELDGYM_LOGO_SVG, unsafe_allow_html=True)
    st.caption("24/7 Fitness • Datová platforma")

    st.markdown(
        """
        <div class="sidebar-nav">
            <a href="#prehled-kpi">📊 Přehled KPI</a>
            <a href="#aktualni-trend">📈 Aktuální trend</a>
            <a href="#vytizenost-v-case">🕒 Vytíženost v čase</a>
            <a href="#podil-tarifu-a-aktivit">🎯 Tarify a aktivity</a>
            <a href="#tabulka-churnu">⚠️ Riziko odchodu (Churn)</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("#### 🔍 Filtry dat")
    selected_dates = st.slider(
        "Období pro filtrování",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD.MM.YYYY",
    )
    activity_type = st.selectbox("Aktivita", list_activities)
    tariff_type = st.selectbox("Tarif", list_tariffs)

# HEADER & OVERVIEW
st.markdown('<div id="prehled-kpi"></div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="fg-hero-header">'
    f'<div class="fg-hero-left">'
    f'{FIELDGYM_LOGO_SVG}'
    f'<div class="fg-hero-divider"></div>'
    f'<div>'
    f'<div class="fg-hero-title">Datová platforma FieldGym</div>'
    f'<div class="fg-hero-subtitle">Přehled návštěvnosti, vytíženosti, tarifů a retence členů</div>'
    f'</div>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="section-desc"><b>Přehled klíčových ukazatelů (KPI):</b> Karty níže shrnují aktuální kondici fitka – počet unikátních návštěvníků za posledních 30 dní v porovnání s předchozím třicetidenním obdobím, včerejší návštěvnost vůči dlouhodobému dennímu průměru a celkový počet aktivních členů oproti minulému měsíci.</p>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.metric(
        label="Návštěvnost (posledních 30 dní)",
        value=f"{visitors_last_30_days:,}",
        delta=f"{visitors_delta_pct:+.1f} % vs předchozích 30 dní",
        border=False,
    )

with col2:
    st.metric(
        label="Včerejší návštěvnost",
        value=f"{visitors_yesterday:,}",
        delta=f"{visitors_yesterday_delta_pct:+.1f} % vs denní průměr",
        delta_color="normal",
        border=False,
    )

with col3:
    st.metric(
        label="Aktivní členové celkem",
        value=f"{members_active_currently:,}",
        delta=f"{members_delta_pct:+.1f} % vs předchozí měsíc",
        border=False,
    )

st.write("")

# SECTION: TREND
st.markdown('<div id="aktualni-trend"></div>', unsafe_allow_html=True)
st.subheader('📈 Aktuální trend návštěvnosti', divider='gray')
st.markdown(
    '<p class="section-desc"><b>Co graf ukazuje:</b> Spojnicový graf zobrazuje vývoj týdenního počtu unikátních návštěvníků v čase. Pomáhá odhalit sezónní výkyvy, dlouhodobý růst či pokles zájmu. Po najetí myší na křivku se zobrazí konkrétní číslo týdne, datum začátku týdne a přesný počet návštěvníků.</p>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    st.plotly_chart(current_trend_chart, use_container_width=True, theme=None)

st.write("")

# SECTION: OCCUPANCY
st.markdown('<div id="vytizenost-v-case"></div>', unsafe_allow_html=True)
st.subheader('🕒 Vytíženost v čase', divider='gray')
st.markdown(
    '<p class="section-desc"><b>Co graf ukazuje:</b> Teplotní mapa (heatmapa) znázorňuje rozložení návštěv podle dne v týdnu (Pondělí–Neděle) a denní hodiny. Tmavě petrolejová pole označují nejvytíženější časy (špičky), zatímco světlá pole ukazují klidnější hodiny s volnou kapacitou.</p>',
    unsafe_allow_html=True,
)
with st.container(border=True):
    st.plotly_chart(occupancy_chart, use_container_width=True, theme=None)

st.write("")

# SECTION: TARIFFS & ACTIVITIES
st.markdown('<div id="podil-tarifu-a-aktivit"></div>', unsafe_allow_html=True)
st.subheader('🎯 Podíl tarifů a aktivit', divider='gray')
st.markdown(
    '<p class="section-desc"><b>Co grafy ukazují:</b> Dvojice prstencových grafů porovnává strukturu návštěv podle typu tréninkové aktivity a rozložení členských tarifů. Po najetí kurzorem na libovolnou výseč se zobrazí přesný počet návštěv či členů i procentuální podíl.</p>',
    unsafe_allow_html=True,
)
col1, col2 = st.columns(2, gap="medium")
with col1:
    with st.container(border=True):
        st.plotly_chart(pie_chart_activities, use_container_width=True, theme=None)
        st.markdown(
            '<div class="chart-caption">💡 <b>Podíl aktivit:</b> Zobrazuje, které tréninkové zóny a lekce generují největší podíl celkových návštěv ve fitku.</div>',
            unsafe_allow_html=True,
        )
with col2:
    with st.container(border=True):
        st.plotly_chart(pie_chart_tariffs, use_container_width=True, theme=None)
        st.markdown(
            '<div class="chart-caption">💡 <b>Podíl tarifů:</b> Ukazuje zastoupení jednotlivých typů členství a permanentek mezi návštěvníky fitka.</div>',
            unsafe_allow_html=True,
        )

st.write("")

# SECTION: CHURN TABLE
st.markdown('<div id="tabulka-churnu"></div>', unsafe_allow_html=True)
st.subheader('⚠️ Tabulka churnu (riziko odchodu)', divider='gray')
st.markdown(
    '<p class="section-desc"><b>Co tabulka ukazuje:</b> Přehled členů s rizikem odchodu (tzv. <i>churn</i>), kteří fitko delší dobu nenavštívili. Pro každého člena uvádí celkový počet historických návštěv, datum první a poslední návštěvy a počet dní od posledního vstupu – slouží jako podklad pro retenční oslovení.</p>',
    unsafe_allow_html=True,
)

churn_rows_html = []
for _, row in df_churn.iterrows():
    cells = []
    for col in df_churn.columns:
        val = row[col]
        if col == "Dny od poslední návštěvy":
            cells.append(f'<td><span class="churn-badge">{val} dní</span></td>')
        else:
            cells.append(f"<td>{val}</td>")
    churn_rows_html.append(f"<tr>{''.join(cells)}</tr>")

churn_headers_html = "".join(f"<th>{col}</th>" for col in df_churn.columns)
churn_table_html = f"""
<div class="churn-table-wrapper">
    <table class="churn-table">
        <thead>
            <tr>{churn_headers_html}</tr>
        </thead>
        <tbody>
            {''.join(churn_rows_html)}
        </tbody>
    </table>
</div>
"""
st.markdown(churn_table_html, unsafe_allow_html=True)





