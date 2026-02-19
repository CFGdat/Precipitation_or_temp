import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. КОНСТАНТИ
FILE_TO_LOAD = 'WEB_AGG_DATA.parquet'
RAW_FILE_TO_LOAD = 'WEB_FINAL_READY.parquet'
ETALON_YEAR = '2025'

# 2. ЗАВАНТАЖЕННЯ ДАНІВ
@st.cache_data
def load_data():
    df = pd.read_parquet(FILE_TO_LOAD)
    date_col = 'date' if 'date' in df.columns else 'plot_date'
    df[date_col] = pd.to_datetime(df[date_col])
    df['year_str'] = df['year'].astype(str)
    df['plot_date'] = df[date_col].map(lambda d: d.replace(year=2024))
    df['hover_date'] = df['plot_date'].dt.strftime('%d-%b')
    if 'day' in df.columns:
        df['decade'] = df['day'].apply(lambda x: 1 if x <= 10 else (2 if x <= 20 else 3))
    return df

@st.cache_data
def load_raw_data():
    try:
        df_raw = pd.read_parquet(RAW_FILE_TO_LOAD)
        if 'date' in df_raw.columns:
            df_raw['date'] = pd.to_datetime(df_raw['date'])
        return df_raw
    except FileNotFoundError:
        return pd.DataFrame()

# 3. КОЛІРНА СХЕМА
def get_colors(df):
    all_years = sorted(df['year_str'].unique())
    palette = px.colors.qualitative.Safe
    return {y: ("red" if y == ETALON_YEAR else palette[i % len(palette)]) 
            for i, y in enumerate(all_years)}

# 4. УНІВЕРСАЛЬНА СТИЛІЗАЦІЯ (ПОВЕРНУТО СТАНДАРТНУ ЛЕГЕНДУ)
def apply_style(fig, etalon=ETALON_YEAR):
    for trace in fig.data:
        if hasattr(trace, 'line') and trace.line is not None:
            trace.line.width = 3.5 if trace.name == etalon else 1.8
        if trace.type == 'bar':
            trace.marker.line.width = 0.5
            trace.marker.line.color = 'white'

    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=40, b=10, l=10, r=10),
        # ПРИБРАНО ЖОРСТКЕ ПОЗИЦІОНУВАННЯ ЗВЕРХУ
        legend=dict(title_text=""), 
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# 5. СЛОВНИК МЕТРИК
def get_metrics_dict():
    return {
        "GDD (Ефективні Т > 10)": "Sum_T_active",
        "Сума Т (якщо Т > 0)": "Sum_T_eff_0",
        "Сума Т (якщо Т > 10)": "Sum_T_eff_10",
        "Накопичені опади": "Sum_Precipitation",
        "Щоденні опади": "precipitation",
        "Мін. температура": "min",
        "Макс. температура": "max",
        "Сер. температура": "mean"
    }