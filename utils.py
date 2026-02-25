import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. КОНСТАНТИ ТА ШЛЯХИ
FILE_TO_LOAD = 'WEB_AGG_DATA.parquet'             # Агреговані дані для швидких графіків
FIELD_SUMMARY_FILE = 'WEB_FIELD_SUMMARY.parquet'  # Готові зведені дані по полях
ETALON_YEAR = '2025'

# 2. ЗАВАНТАЖЕННЯ АГРЕГОВАНИХ ДАНИХ (Для основних графіків)
@st.cache_data
def load_data():
    if not os.path.exists(FILE_TO_LOAD):
        st.error(f"Файл {FILE_TO_LOAD} не знайдено!")
        return pd.DataFrame()
        
    df = pd.read_parquet(FILE_TO_LOAD)
    
    # Визначаємо колонку з датою
    date_col = 'date' if 'date' in df.columns else 'plot_date'
    df[date_col] = pd.to_datetime(df[date_col])
    
    df['year_str'] = df['year'].astype(str)
    
    # Синхронізація дат на 2024 рік для накладання графіків
    df['plot_date'] = df[date_col].map(lambda d: d.replace(year=2024))
    df['hover_date'] = df['plot_date'].dt.strftime('%d-%b')
    
    # Розрахунок декад (якщо є колонка дня)
    if 'day' in df.columns:
        df['decade'] = df['day'].apply(lambda x: 1 if x <= 10 else (2 if x <= 20 else 3))
    
    return df

# 3. ШВИДКЕ ЗАВАНТАЖЕННЯ ГОТОВОЇ ТАБЛИЦІ ПО ПОЛЯХ (Для таблиць)
@st.cache_data
def load_field_summary():
    """Миттєво завантажує вже прораховану агрегацію."""
    if not os.path.exists(FIELD_SUMMARY_FILE):
        st.error(f"Файл {FIELD_SUMMARY_FILE} не знайдено! Запусти скрипт precompute_summary.py")
        return pd.DataFrame()
    return pd.read_parquet(FIELD_SUMMARY_FILE)

# 4. КОЛІРНА СХЕМА
def get_colors(df):
    all_years = sorted(df['year_str'].unique())
    palette = px.colors.qualitative.Safe
    return {y: ("red" if y == ETALON_YEAR else palette[i % len(palette)]) 
            for i, y in enumerate(all_years)}

# 5. УНІВЕРСАЛЬНА СТИЛІЗАЦІЯ
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
        legend=dict(title_text=""),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# 6. СЛОВНИК МЕТРИК
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
