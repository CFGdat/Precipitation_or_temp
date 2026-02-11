import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- НАЛАШТУВАННЯ ---
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
    
    /* Зменшуємо відступи між елементами сайдбару */
    [data-testid="stSidebar"] .stElementContainer {
        margin-bottom: -0.5rem;
    }
    
    /* Компактні чекбокси */
    .stCheckbox { margin-top: -5px; }
    
    /* Розділювачі */
    hr { margin: 1rem 0; }
    
    /* Графіки */
    .plotly-graph-div {
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* Прибираємо зайві відступи в колонках */
    div[data-testid="column"] { padding: 0; }
</style>
""", unsafe_allow_html=True)

# --- ЗАВАНТАЖЕННЯ ---
@st.cache_data
def load_data():
    try:
        df = pd.read_parquet("data.parquet")
        df['Date'] = pd.to_datetime(df['Date'])
        df['PlotDate'] = pd.to_datetime(df['PlotDate'])
        
        # Чистка
        df = df.dropna(subset=['Регіон', 'Блок'])
        # Видаляємо текстові "nan", "none" і пусті
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
    # 🎛️ SIDEBAR (КОМПАКТНИЙ)
    # ==========================================
    with st.sidebar:
        st.header("🎛️ Фільтри")
        
        # --- 1. РЕГІОН ---
        st.caption("📍 **Регіон**") 
        all_regions = sorted(df_raw['Регіон'].astype(str).unique())
        
        # Кнопки
        cr1, cr2 = st.columns(2)
        if cr1.button("✅ Всі", key="reg_all", use_container_width=True):
            for r in all_regions: st.session_state[f"reg_{r}"] = True
        if cr2.button("❌ Ні", key="reg_none", use_container_width=True):
            for r in all_regions: st.session_state[f"reg_{r}"] = False

        regions_to_filter = []
        
        # !!! ВИПРАВЛЕННЯ ПОМИЛКИ !!!
        # Створюємо контейнер по-різному, щоб не передавати height=None
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
        
        if not regions_to_filter: st.warning("Оберіть регіон")

        st.divider()

        # --- 2. БЛОК ---
        st.caption("🚜 **Блок**")
        avail_blocks_df = df_raw[df_raw['Регіон'].isin(regions_to_filter)]
        
        # Додаткова фільтрація сміття
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

        # --- 3. РОКИ (3 КОЛОНКИ) ---
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

        if not years_to_filter: st.warning("Оберіть рік")

    # ==========================================
    # ОБРОБКА
    # ==========================================
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
        df_chart['Year_Str'] = df_chart['Рік'].astype(str)

        # Кольори
        unique_yrs = sorted(df_chart['Рік'].unique())
        palette = ['#2980b9', '#f39c12', '#27ae60', '#8e44ad', '#7f8c8d', '#d35400', '#16a085']
        color_map = {}
        for i, y in enumerate(unique_yrs):
            color_map[str(y)] = '#e74c3c' if y == 2025 else palette[i % len(palette)]

        # Стилі
        def apply_style(fig):
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=40, b=50, l=40, r=20),
            )
            return fig

        # ==========================================
        # ВІЗУАЛІЗАЦІЯ
        # ==========================================
        tab1, tab2, tab3, tab4 = st.tabs(["🌡️ Температура", "💧 Опади", "📋 Деталі", "🛠️ Конструктор"])

        # === TAB 1: ТЕМПЕРАТУРА ===
        with tab1:
            fig_temp = make_subplots(
                rows=2, cols=2,
                specs=[[{}, {}], [{"colspan": 2}, None]], 
                subplot_titles=("Накопичення t > 0°C", "Накопичення t > 10°C", "Мінімальна температура (t min)"),
                vertical_spacing=0.15
            )
            for year in unique_yrs:
                if year not in years_to_filter: continue
                yd = df_chart[df_chart['Рік'] == year]
                if yd.empty: continue
                c = color_map.get(str(year), 'grey')
                is_2025 = (year == 2025)
                w = 3.5 if is_2025 else 1.5
                hover_simple = "<b>%{y:.2f}</b><extra></extra>" 

                if 'Значення t>0' in df_chart.columns:
                    fig_temp.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['Значення t>0'], name=str(year), mode='lines', line=dict(color=c, width=w), legendgroup=str(year), showlegend=True, hovertemplate=hover_simple), row=1, col=1)
                if 'Значення t>10' in df_chart.columns:
                    fig_temp.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['Значення t>10'], name=str(year), mode='lines', line=dict(color=c, width=w), legendgroup=str(year), showlegend=False, hovertemplate=hover_simple), row=1, col=2)
                if 't min' in df_chart.columns:
                    fig_temp.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['t min'], name=str(year), mode='lines', line=dict(color=c, width=w), legendgroup=str(year), showlegend=False, hovertemplate=hover_simple), row=2, col=1)

            fig_temp.add_hrect(y0=-40, y1=0, fillcolor="#3498db", opacity=0.08, line_width=0, layer="below", row=2, col=1)
            fig_temp.add_hline(y=0, line_dash="dash", line_color="#2980b9", opacity=0.5, row=2, col=1)
            fig_temp.update_layout(height=700, hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"), margin=dict(t=30, b=50, l=40, r=20))
            fig_temp.update_xaxes(dtick="M1", tickformat="%d/%m", showgrid=False)
            fig_temp.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f5f5f5')
            st.plotly_chart(fig_temp, use_container_width=True)

        # === TAB 2: ОПАДИ ===
        with tab2:
            fig_precip = make_subplots(rows=2, cols=1, subplot_titles=("Щоденні опади (Вересень)", "Накопичувальні опади"), vertical_spacing=0.2)
            for year in unique_yrs:
                if year not in years_to_filter: continue
                yd = df_chart[df_chart['Рік'] == year]
                if yd.empty: continue
                c = color_map.get(str(year), 'grey')
                is_2025 = (year == 2025)
                hover_rain = "<b>%{y:.1f}</b> мм<extra></extra>"

                if 'Precipitation' in df_chart.columns:
                    yd_sep = yd[yd['Date'].dt.month == 9]
                    if not yd_sep.empty:
                        fig_precip.add_trace(go.Bar(x=yd_sep['PlotDate'], y=yd_sep['Precipitation'], name=str(year), marker_color=c, opacity=1 if is_2025 else 0.6, legendgroup=str(year), showlegend=True, hovertemplate=hover_rain), row=1, col=1)

                if 'Precipitation Total' in df_chart.columns:
                    fig_precip.add_trace(go.Scatter(x=yd['PlotDate'], y=yd['Precipitation Total'], name=str(year), mode='lines', line=dict(color=c, width=3.5 if is_2025 else 1.5), legendgroup=str(year), showlegend=False, hovertemplate=hover_rain), row=2, col=1)

            fig_precip.update_layout(height=700, hovermode="x unified", barmode='group', bargap=0.1, bargroupgap=0.0, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"), margin=dict(t=30, b=50, l=40, r=20))
            fig_precip.update_xaxes(dtick="M1", tickformat="%d/%m", showgrid=False)
            fig_precip.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f5f5f5')
            st.plotly_chart(fig_precip, use_container_width=True)

        # === TAB 3: ДЕТАЛІ ===
        with tab3:
            display_cols = ['Date', 'Регіон', 'Блок', 'Рік'] + cols
            final_display_cols = [c for c in display_cols if c in df_filtered.columns]
            df_display = df_filtered[final_display_cols].copy()
            for c in cols:
                if c in df_display.columns: df_display[c] = df_display[c].round(2)
            
            # Таблиця на всю ширину
            st.dataframe(
                df_display.sort_values(['Date', 'Регіон']), 
                use_container_width=True, 
                height=700, 
                hide_index=True
            )

        # === TAB 4: КОНСТРУКТОР ===
        with tab4:
            c1, c2 = st.columns(2)
            with c1: y_left = st.selectbox("Ліва вісь", cols, index=0)
            with c2: y_right = st.selectbox("Права вісь", cols, index=1 if len(cols)>1 else 0)
            
            fig_combo = go.Figure()
            for year in unique_yrs:
                if year not in years_to_filter: continue
                yd = df_chart[df_chart['Рік'] == year]
                if yd.empty: continue
                c = color_map.get(str(year), 'grey')
                is_2025 = (year == 2025)
                fig_combo.add_trace(go.Scatter(x=yd['PlotDate'], y=yd[y_left], name=f"{y_left} {year}", mode='lines', line=dict(color=c, width=3.5 if is_2025 else 1.5), yaxis='y1', hovertemplate="<b>%{y:.2f}</b><extra></extra>"))
                fig_combo.add_trace(go.Bar(x=yd['PlotDate'], y=yd[y_right], name=f"{y_right} {year}", marker_color=c, opacity=0.8 if is_2025 else 0.3, yaxis='y2', hovertemplate="<b>%{y:.2f}</b><extra></extra>"))

            fig_combo.update_layout(title=dict(text=f"{y_left} vs {y_right}", font=dict(size=16)), xaxis=dict(tickformat="%d/%m", showgrid=False), yaxis=dict(title=y_left, side="left", showgrid=True, gridcolor='#f5f5f5'), yaxis2=dict(title=y_right, side="right", overlaying="y", showgrid=False), hovermode="x unified", height=550, barmode='group', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"), margin=dict(l=60, r=60, t=60, b=100))
            if y_left == 't min': fig_combo.add_hline(y=0, line_dash="dash", line_color="blue", opacity=0.5)
            st.plotly_chart(fig_combo, use_container_width=True)