import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ЗАХИСТ ПАРОЛЕМ ---
def check_password():
    """Повертає True, якщо користувач ввів правильний пароль."""
    def password_entered():
        if st.session_state["password"] == "Agro2025": # ВСТАНОВІТЬ СВІЙ ПАРОЛЬ ТУТ
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Видаляємо пароль із session_state
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Показуємо поле для введення
        st.text_input("Введіть пароль для доступу", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Пароль невірний
        st.text_input("Введіть пароль для доступу", type="password", on_change=password_entered, key="password")
        st.error("😕 Невірний пароль")
        return False
    else:
        # Пароль вірний
        return True

# Перевірка пароля перед запуском всього іншого
if check_password():

    # --- НАЛАШТУВАННЯ ---
    st.set_page_config(page_title="AgroMonitor Pro", layout="wide", page_icon="🌾")

    # --- CSS ---
    st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        [data-testid="stSidebar"] { 
            background-color: #ffffff; 
            border-right: 1px solid #e0e0e0;
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] .stElementContainer { margin-bottom: -0.5rem; }
        .stCheckbox { margin-top: -5px; }
        hr { margin: 1rem 0; }
        .plotly-graph-div {
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 10px;
            margin-bottom: 10px;
        }
        div[data-testid="column"] { padding: 0; }
    </style>
    """, unsafe_allow_html=True)

    # --- ЗАВАНТАЖЕННЯ ДАНИХ ---
    @st.cache_data
    def load_data():
        try:
            df = pd.read_parquet("data.parquet")
            df['Date'] = pd.to_datetime(df['Date'])
            df['PlotDate'] = pd.to_datetime(df['PlotDate'])
            df = df.dropna(subset=['Регіон', 'Блок'])
            df = df[~df['Блок'].astype(str).str.lower().isin(['nan', 'none', ''])]
            df = df[df['Блок'].astype(str).str.strip() != '']
            return df
        except FileNotFoundError:
            return None

    df_raw = load_data()

    # --- HEADER ---
    c1, c2 = st.columns([0.5, 10])
    with c1: st.image("https://cdn-icons-png.flaticon.com/512/2529/2529969.png", width=60)
    with c2: st.title("Agro Clima Dashboard")

    if df_raw is None:
        st.error("⚠️ Файл data.parquet не знайдено.")
    else:
        # --- SIDEBAR ---
        with st.sidebar:
            st.header("🎛️ Фільтри")
            
            st.caption("📍 **Регіон**") 
            all_regions = sorted(df_raw['Регіон'].astype(str).unique())
            
            cr1, cr2 = st.columns(2)
            if cr1.button("✅ Всі", key="reg_all", use_container_width=True):
                for r in all_regions: st.session_state[f"reg_{r}"] = True
            if cr2.button("❌ Ні", key="reg_none", use_container_width=True):
                for r in all_regions: st.session_state[f"reg_{r}"] = False

            regions_to_filter = []
            if len(all_regions) > 5:
                reg_container = st.container(height=150, border=False)
            else:
                reg_container = st.container(border=False)

            with reg_container:
                for r in all_regions:
                    key = f"reg_{r}"
                    if key not in st.session_state: st.session_state[key] = True
                    if st.checkbox(r, key=key):
                        regions_to_filter.append(r)
            
            st.divider()

            # --- БЛОК ---
            st.caption("🚜 **Блок**")
            avail_blocks_df = df_raw[df_raw['Регіон'].isin(regions_to_filter)]
            raw_blocks = avail_blocks_df['Блок'].unique()
            valid_blocks = [str(b) for b in raw_blocks if str(b).lower() not in ['nan', 'none', '']]
            avail_blocks = sorted(valid_blocks)
            
            use_all_blocks = st.checkbox("Всі доступні блоки", value=True)
            if use_all_blocks:
                blocks_to_filter = avail_blocks
            else:
                sel_blocks = st.multiselect("Вибір блоків:", avail_blocks, label_visibility="collapsed")
                blocks_to_filter = sel_blocks if sel_blocks else avail_blocks

            st.divider()

            # --- РОКИ ---
            st.caption("📅 **Роки**")
            all_years = sorted(df_raw['Рік'].unique())
            cy1, cy2 = st.columns(2)
            if cy1.button("✅ Всі", key="yr_all", use_container_width=True):
                for y in all_years: st.session_state[f"chk_{y}"] = True
            if cy2.button("❌ Ні", key="yr_none", use_container_width=True):
                for y in all_years: st.session_state[f"chk_{y}"] = False

            years_to_filter = []
            y_cols = st.columns(3) 
            for i, year in enumerate(all_years):
                key = f"chk_{year}"
                if key not in st.session_state: st.session_state[key] = True
                if y_cols[i % 3].checkbox(str(year), key=key):
                    years_to_filter.append(year)

        # --- ОБРОБКА ТА ВІЗУАЛІЗАЦІЯ (Решта вашого коду) ---
        mask = df_raw['Рік'].isin(years_to_filter)
        mask &= df_raw['Регіон'].isin(regions_to_filter)
        mask &= df_raw['Блок'].isin(blocks_to_filter)
        df_filtered = df_raw[mask].copy()

        if df_filtered.empty:
            st.info("Дані відсутні.")
        else:
            metrics_cols = ['Precipitation Total', 'Precipitation', 'Значення t>0', 'Значення t>10', 't min']
            cols = [c for c in metrics_cols if c in df_filtered.columns]
            df_chart = df_filtered.groupby(['Рік', 'PlotDate', 'Date'], as_index=False)[cols].mean()
            df_chart = df_chart.sort_values(by='PlotDate')
            
            tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Температура", "💧 Опади", "📋 Деталі", "🛠️ Конструктор"])
            
            # (Тут залишається вся ваша логіка з графіками та таблицями...)
            with tab1:
                st.write("Тут будуть ваші графіки температури")
                # Вставте свій блок побудови fig_temp
                
            with tab3:
                st.dataframe(df_filtered, use_container_width=True)
