# IMPORT LIBRARIES
import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import psycopg2
import plotly.express as px

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

# MAIN DATAFRAME
try:
    query = "SELECT * FROM fct_fieldgym_data"
    df = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno {len(df)} řádků z databáze!")
except Exception as e: 
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

# TIME/DATE DATAFRAME
try:
    query = "SELECT DISTINCT * FROM fct_wdays_time"
    df_wdays = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno {len(df_wdays)} řádků z databáze!")
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

# FAVORITE ACTIVITIES
try:
    query = "SELECT DISTINCT activity_type FROM fct_favorite_tariffs"
    df_activities = pd.read_sql(query, con=engine)
    list_activities = ["Vše"] + df_activities['activity_type'].dropna().tolist()
    print(f"✅Úspěšně načteno {len(df_activities)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    list_activities = ["Vše"]
    exit()

# FAVORITE TARIFFS
try:
    query = "SELECT DISTINCT tariff_type FROM fct_favorite_tariffs"
    df_tariffs = pd.read_sql(query, con=engine)
    list_tariffs = ["Vše"] + df_tariffs['tariff_type'].dropna().tolist()
    print(f"✅Úspěšně načteno {len(df_tariffs)} řádků z databáze!")
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    list_tariffs = ["Vše"]
    exit()

# DATES
try:
    query = "SELECT MIN(date_only) AS min_date, MAX(date_only) AS max_date FROM fct_fieldgym_data"
    df_dates = pd.read_sql(query, con=engine)
    print(f"✅Úspěšně načteno rozsah dat z databáze!")
    min_date = df_dates["min_date"].iloc[0]
    max_date = df_dates["max_date"].iloc[0]
except Exception as e:
    print(f"❌Chyba při načítání dat z databáze: {e}")
    exit()

# CHARTS
## Aktuální trend návštěvnosti - line chart
current_trend_chart = px.line(
    df.groupby('date_only')['member_id'].nunique().reset_index(),
    x='date_only',
    y='member_id',
    labels={'date_only': 'Datum', 'member_id': 'Počet návštěv'},
    title='Aktuální trend návštěvnosti',
)
current_trend_chart.update_layout(
    font=dict(family="Arial", size=12, color="black"),
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    title_font_color="black",
    xaxis=dict(title_font_color="black", tickfont=dict(color="black")),
    yaxis=dict(title_font_color="black", tickfont=dict(color="black")),
)

## Vytíženost v čase - heatmap
occupancy_chart = px.density_heatmap(df_wdays, x='hour', y='den_v_tydnu', z='member_id', histfunc='count', color_continuous_scale='Viridis', labels={'hour': 'Hodina', 'den_v_tydnu': 'Den v týdnu', 'member_id': 'Počet návštěv'}, title='Vytíženost v čase')

# FORMATTING
## Světle modro-bílá (prostřední část): #F0F8F8; Tmavě modro-zelená / petrolejová (spodní část): #112E35
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFFFF;
    }

    [data-testid="stSidebar"] {
        background-color: #112E35;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    .stApp p, .stApp span, .stApp label, .stApp div {
        color: #112E35;
    }

    [data-testid="stMetricDelta"] {
        padding: 4px 10px !important;
        border-radius: 6px !important;
        display: inline-flex !important;
        align-items: center !important;
        width: fit-content !important;
        background-color: #F0F8F8 !important;
        color: #112E35 !important;
    }

    [data-testid="stMetricDelta"]:has(svg path[d*="M4"], svg path[d*="m4"]) {
        background-color: #F0F8F8 !important;
        color: #112E35 !important;
    }

    [data-testid="stMetricDelta"]:has(svg path[d*="M20"], svg path[d*="m20"]) {
        background-color: #F0F8F8 !important;
        color: #112E35 !important;
    }

    [data-testid="stMetricDelta"] div,
    [data-testid="stMetricDelta"] span {
        color: inherit !important;
    }

    [data-testid="stMetricDelta"] svg {
        fill: currentColor !important;
        color: inherit !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# SIDEBAR
selected_dates = st.sidebar.slider(
    "Období pro filtrování",
    value=(min_date, max_date),  # Výchozí rozsah (od nejstaršího do nejnovějšího)
    min_value=min_date,           # Minimální povolené datum v kalendáři
    max_value=max_date            # Maximální povolené datum v kalendáři
)
activity_type = st.sidebar.selectbox("Aktivita", list_activities) # activity type
tariff_type = st.sidebar.selectbox("Tarif", list_tariffs) # tariff type

# TEXT
st.title('Datová platforma FieldGym')

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Návštěvnost posledních 30 dní",
        value=f"{visitors_last_30_days:,}",
        delta=f"{visitors_delta_pct:.1f} % vs předchozích 30 dní",
        border=False
    )

with col2:
    st.metric(
        label="Včerejší návštěvnost",
        value=f"{visitors_yesterday:,}",
        delta=f"{visitors_yesterday_delta_pct:.1f} % vs průměr",
        delta_color="normal",
        border=False
    )

with col3:
    st.metric(
        label="Aktivní členové",
        value=f"{members_active_currently:,}",
        delta=f"{members_delta_pct:.1f} % vs předchozí měsíc",
        border=False
    )

st.header('O aplikaci', divider='gray')
st.text('Aplikace slouží k vizualizaci dat z FieldGym databáze. Ukazuje základní údaje o návštěvnosti, vytíženosti a oblíbených aktivitách ve fitku.')
st.header('Aktuální trend', divider='gray')
st.plotly_chart(current_trend_chart)
st.header('Vytíženost v čase', divider='gray')
st.plotly_chart(occupancy_chart)
st.text('Vizuál ukazuje vytíženost fitka v jednotlivých dnech a jednotlivých hodnách. Časové období lze upravit pomocí filtru v levém panelu.')
st.header('Podíl tarifů a aktivit', divider='gray')
st.text('Grafy ukazují podíl jednotlivých tarifů a aktivit mezi členy fitka. Časové období, aktivity a tarify lze upravit pomocí filtru v levém panelu.')
st.header('Tabulka churnu', divider='gray')
st.text('Tabulka ukazuje členy, kteří přestali (nebo možná brzy přestanou) navštěvovat fitko. Tabulku lze filtrovat podle aktivit a tarifů v levém panelu. Podle časového období filtrovat nelze')





