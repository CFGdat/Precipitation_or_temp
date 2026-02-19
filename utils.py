import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import glob
import os

# 1. КОНСТАНТИ ТА ШЛЯХИ
FILE_TO_LOAD = 'WEB_AGG_DATA.parquet'      # Агреговані дані для швидких графіків
CHUNKS_PATH = 'data_chunks/*.parquet'       # Шлях до твоїх частин по 25 МБ
ETALON_YEAR = '2025'

# 2. ЗАВАНТАЖЕННЯ АГРЕГОВАНИХ ДАНИХ (Для основних табів)
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

# 3. ЗАВАНТАЖЕННЯ ДЕТАЛЬНИХ ДАНИХ (Збирання частин по 25 МБ)
@st.cache_data
def load_raw_data():
    """
    Збирає всі файли з папки data_chunks і склеює їх в один DataFrame.
    Це дозволяє обійти ліміт завантаження файлів на GitHub.
    """
    try:
        # Шукаємо всі parquet-файли в папці
        all_parts = glob.glob(CHUNKS_PATH)
        
        if not all_parts:
            # Якщо частин немає, повертаємо порожній DF (або агрегований як фолбек)
            return pd.DataFrame()
        
        # Читаємо кожну частину та додаємо в список
        chunks = []
        for file in all_parts:
            chunks.append(pd.read_parquet(file))
            
        # Зшиваємо все в один масив
        df_raw = pd.concat(chunks, ignore_index=True)
        
        # Конвертуємо дати після зшивання
        if 'date' in df_raw.columns:
            df_raw['date'] = pd.to_datetime(df_raw['date'])
            
        # Сортуємо, щоб дані в таблицях йшли по порядку
        df_raw = df_raw.sort_values(['year', 'date'])
        
        return df_raw
    except Exception as e:
        st.error(f"Критична помилка збірки даних: {e}")
        return pd.DataFrame()

# 4. КОЛІРНА СХЕМА
def get_colors(df):
    all_years = sorted(df['year_str'].unique())
    palette = px.colors.qualitative.Safe
    # Еталон завжди червоний, решта - за списком
    return {y: ("red" if y == ETALON_YEAR else palette[i % len(palette)]) 
            for i, y in enumerate(all_years)}

# 5. УНІВЕРСАЛЬНА СТИЛІЗАЦІЯ (Безпечна для всіх типів графіків)
def apply_style(fig, etalon=ETALON_YEAR):
    """
    Налаштовує товщину ліній та легенду. 
    Включає перевірку наявності атрибутів, щоб не ламати Bar Charts.
    """
    for trace in fig.data:
        # Стиль для ліній (Scatter)
        if hasattr(trace, 'line') and trace.line is not None:
            trace.line.width = 3.5 if trace.name == etalon else 1.8
        
        # Стиль для стовпчиків (Bar)
        if trace.type == 'bar':
            trace.marker.line.width = 0.5
            trace.marker.line.color = 'white'

    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(title_text=""), # Прибираємо заголовок легенди для чистоти
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# 6. СЛОВНИК МЕТРИК (Твоє джерело правди)
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
