import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- 1. ФУНКЦІЯ ПЕРЕВІРКИ ПАРОЛЯ ---
def check_password():
    """Повертає True, якщо користувач ввів правильний пароль."""
    def password_entered():
        # Перевіряємо, чи введений пароль збігається з паролем у Secrets
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Видаляємо пароль з пам'яті
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Перший запуск: малюємо форму
        st.markdown("<h2 style='text-align: center;'>🔒 Доступ обмежено</h2>", unsafe_allow_html=True)
        st.text_input("Введіть пароль для перегляду дашборду", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Пароль невірний
        st.markdown("<h2 style='text-align: center;'>🔒 Доступ обмежено</h2>", unsafe_allow_html=True)
        st.text_input("Введіть пароль для перегляду дашборду", type="password", on_change=password_entered, key="password")
        st.error("😕 Невірний пароль. Спробуйте ще раз.")
        return False
    else:
        # Пароль вірний
        return True

# --- ЗАПУСК ДОДАТКА ПІСЛЯ ПЕРЕВІРКИ ---
if check_password():

    # --- НАЛАШТУВАННЯ СТОРІНКИ ---
    st.set_page_config(page_title="AgroMonitor Pro", layout="wide", page_icon="🌾")

    # --- CSS (КОМПАКТНИЙ РЕЖИМ) ---
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
            
            # Чистка даних
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
        # ==========================================
        # 🎛️ SIDEBAR
        # ==========================================
        with st.sidebar:
            st.header("🎛️ Фільтри")
            
            # --- 1. РЕГІОН ---
            st.caption("📍 **Регіон**") 
            all_regions = sorted(df_raw['Регіон'].astype(str).unique())
            
            cr1, cr2 = st.columns(2)
            if cr1.button("✅ Всі", key="reg_all", use_container_width=True):
                for r in all_regions: st.session_state[f"reg_{r}"] = True
            if cr2.button("❌ Ні", key="reg_none", use_container_width=True):
                for r in all_regions: st.session_state[f"reg_{r}"] = False

            regions_to_filter = []
            # Перевірка для коректного height
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

            # --- 2. БЛОК ---
            st.caption("🚜 **Блок**")
            avail_blocks_df = df_raw[df_raw['Регіон'].isin(regions_to_filter)]
            avail_blocks = sorted([str(b) for b in avail_blocks_df['Блок'].unique() if str(b).lower() not in ['nan', 'none', '']])
            
            use_all_blocks = st.checkbox("Всі доступні блоки", value=True)
            if use_all_blocks:
                blocks_to_filter = avail_blocks
            else:
                sel_blocks = st.multiselect("Вибір:", avail_blocks, label_visibility="collapsed")
                blocks_to_filter = sel_blocks if sel_blocks else avail_blocks

            st.divider()

            # --- 3. РОКИ ---
            st.caption("📅 **Роки**")
            all_years = sorted(df_raw['Рік'].unique())
            cy1, cy2 = st.columns(2)
            if cy1.button("✅", key="yr_all", use_container_width=True):
                for y in all_years: st.session_state[f"chk_{y}"] = True
            if cy2.button("❌", key="yr_none", use_container_width=True):
                for y in all_years: st.session_state[f"chk_{y}"] = False

            years_to_filter = []
            y_cols = st.columns(3) 
            for i, year in enumerate(all_years):
                key = f"chk_{year}"
                if key not in st.session_state: st.session_state[key] = True
                if y_cols[i % 3].checkbox(str(year), key=key):
                    years_to_filter.append(year)

        # ==========================================
        # ОБРОБКА ДАНИХ
        # ==========================================
        mask = df_raw['Рік'].isin(years_to_filter)
        mask &= df_raw['Регіон'].isin(regions_to_filter)
        mask &= df_raw['Блок'].isin(blocks_to_filter)
        df_filtered = df_raw[mask].copy()

        if df_filtered.empty:
            st.info("Дані відсутні для обраних фільтрів.")
        else:
            metrics_cols = ['Precipitation Total', 'Precipitation', 'Значення t>0', 'Значення t>10', 't min']
            cols = [c for c in metrics_cols if c in df_filtered.columns]
            
            df_chart = df_filtered.groupby(['Рік', 'PlotDate', 'Date'], as_index=False)[cols].mean()
            df_chart = df_chart.sort_values(by='PlotDate')

            # Кольорова схема
            unique_yrs = sorted(df_chart['Рік'].unique())
            palette = ['#2980b9', '#f39c12', '#27ae60', '#8e44ad', '#7f8c8d', '#d35400', '#16a085']
            color_map = {str(y): ('#e74c3c' if y == 2025 else palette[i % len(palette)]) for i, y in enumerate(unique_yrs)}

            # ==========================================
            # ВІЗУАЛІЗАЦІЯ (TABS)
            # ==========================================
            tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Температура", "💧 Опади", "📋 Деталі", "🛠️ Конструктор"])

            with tab1:
                fig_temp = make_subplots(
                    rows=2, cols=2,
                    specs=[[{}, {}], [{"colspan": 2}, None]], 
                    subplot_titles=("Накопичення t > 0°C", "Накопичення t > 10°C", "Мінімальна температура (t min)"),
                    vertical_spacing=0.15
                )
                for year in unique_yrs:
                    yd = df_chart[df_chart['Рік'] == year]
                    c = color_map.get(str(year))
                    is_2025 = (year == 2025)
                    w = 3.5 if is_2025 else 1.5

                    if 'Значення t>0' in yd.columns:
                        fig_temp.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['Значення t>0'], name=str(year), mode='lines', line=dict(color=c, width=w), legendgroup=str(year)), row=1, col=1)
                    if 'Значення t>10' in yd.columns:
                        fig_temp.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['Значення t>10'], name=str(year), mode='lines', line=dict(color=c, width=w), legendgroup=str(year), showlegend=False), row=1, col=2)
                    if 't min' in yd.columns:
                        fig_temp.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['t min'], name=str(year), mode='lines', line=dict(color=c, width=w), legendgroup=str(year), showlegend=False), row=2, col=1)

                fig_temp.add_hline(y=0, line_dash="dash", line_color="blue", row=2, col=1)
                fig_temp.update_layout(height=700, hovermode="x unified", legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"))
                st.plotly_chart(fig_temp, use_container_width=True)

            with tab2:
                fig_precip = make_subplots(rows=2, cols=1, subplot_titles=("Опади за Вересень (мм)", "Накопичувальні опади"), vertical_spacing=0.2)
                for year in unique_yrs:
                    yd = df_chart[df_chart['Рік'] == year]
                    c = color_map.get(str(year))
                    
                    yd_sep = yd[yd['Date'].dt.month == 9]
                    if not yd_sep.empty:
                        fig_precip.add_trace(go.Bar(x=yd_sep['PlotDate'], y=yd_sep['Precipitation'], name=str(year), marker_color=c, legendgroup=str(year)), row=1, col=1)
                    
                    fig_precip.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['Precipitation Total'], name=str(year), mode='lines', line=dict(color=c, width=3 if year==2025 else 1.5), legendgroup=str(year), showlegend=False), row=2, col=1)

                fig_precip.update_layout(height=700, barmode='group', hovermode="x unified")
                st.plotly_chart(fig_precip, use_container_width=True)

            with tab3:
                st.dataframe(df_filtered.drop(columns=['PlotDate'], errors='ignore'), use_container_width=True, height=600)

            with tab4:
                c1, c2 = st.columns(2)
                y1_sel = c1.selectbox("Ліва вісь", cols, index=0)
                y2_sel = c2.selectbox("Права вісь", cols, index=1 if len(cols)>1 else 0)
                
                fig_custom = go.Figure()
                for year in unique_yrs:
                    yd = df_chart[df_chart['Рік'] == year]
                    c = color_map.get(str(year))
                    fig_custom.add_trace(go.Scatter(x=yd['PlotDate'], y=yd[y1_sel], name=f"{year} {y1_sel}", line=dict(color=c, width=2.5), yaxis='y1'))
                    fig_custom.add_trace(go.Scatter(x=yd['PlotDate'], y=yd[y2_sel], name=f"{year} {y2_sel}", line=dict(color=c, dash='dot'), yaxis='y2', opacity=0.6))
                
                fig_custom.update_layout(height=600, yaxis=dict(title=y1_sel), yaxis2=dict(title=y2_sel, overlaying='y', side='right'))
                st.plotly_chart(fig_custom, use_container_width=True)
