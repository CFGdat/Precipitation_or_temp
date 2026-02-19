import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import get_metrics_dict
import numpy as np

def show(df_chart, color_map, etalon='2025'):
    st.subheader("🛠️ Конструктор порівнянь")
    
    # --- 1. СИНХРОНІЗАЦІЯ З ГЛОБАЛЬНИМ ФІЛЬТРОМ ---
    available_years = sorted(df_chart['year_str'].dropna().unique(), reverse=True)
    
    if not available_years:
        st.warning("Немає доступних даних для вибраних фільтрів.")
        return

    # Якщо глобальний фільтр змінився, скидаємо вибір конструктора на макс. рік
    if "prev_available" not in st.session_state or st.session_state.prev_available != available_years:
        st.session_state.const_sel_years = [available_years[0]]
        st.session_state.prev_available = available_years

    # --- 2. ВІДЖЕТИ КЕРУВАННЯ ---
    sel_years = st.multiselect(
        "📅 Оберіть роки для порівняння:", 
        options=available_years, 
        key="const_sel_years" # Прив'язка до session_state
    )

    if not sel_years:
        st.warning("Будь ласка, оберіть хоча б один рік.")
        return

    st.divider()
    
    m_dict = get_metrics_dict()
    c1, c2, c3 = st.columns([2, 2, 1.5])
    with c1: m1_lab = st.selectbox("📈 Ліва вісь (Лінія)", list(m_dict.keys()), index=0)
    with c2: m2_lab = st.selectbox("📊 Права вісь", list(m_dict.keys()), index=4)
    with c3: chart_type_2 = st.radio("Вигляд правої осі:", ["Пунктир", "Стовпчики"], index=1)

    # --- 3. ПІДГОТОВКА ДАНИХ ТА СИНХРОНІЗАЦІЯ ШКАЛ ---
    m1_col, m2_col = m_dict[m1_lab], m_dict[m2_lab]
    df_sel = df_chart[df_chart['year_str'].isin(sel_years)]
    
    y1_min, y1_max = df_sel[m1_col].min(), df_sel[m1_col].max()
    y2_min, y2_max = df_sel[m2_col].min(), df_sel[m2_col].max()

    def get_synced_range(min_val, max_val, other_min, other_max):
        if min_val >= 0 and other_min >= 0:
            return [0, max_val * 1.1]
        r1 = min_val / max_val if max_val != 0 else 0
        r2 = other_min / other_max if other_max != 0 else 0
        final_ratio = min(r1, r2)
        return [max_val * final_ratio, max_val * 1.1]

    range1 = get_synced_range(y1_min, y1_max, y2_min, y2_max)
    range2 = get_synced_range(y2_min, y2_max, y1_min, y1_max)

    # --- 4. ПОБУДОВА ГРАФІКА ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    for y in sel_years:
        df_y = df_chart[df_chart['year_str'] == y]
        if df_y.empty: continue
        
        # ЛІВА ВІСЬ
        fig.add_trace(go.Scatter(
            x=df_y['plot_date'], y=df_y[m1_col], name=f"{y} {m1_lab}",
            line=dict(color=color_map.get(y, '#1f77b4'), width=3.5 if y == etalon else 2),
            customdata=df_y['hover_date'], hovertemplate="%{y:.1f}"
        ), secondary_y=False)
        
        # ПРАВА ВІСЬ
        if "Стовпчики" in chart_type_2:
            fig.add_trace(go.Bar(
                x=df_y['plot_date'], y=df_y[m2_col], name=f"{y} {m2_lab}",
                marker_color=color_map.get(y, '#ff7f0e'), opacity=0.5,
                customdata=df_y['hover_date'], hovertemplate="%{y:.1f}"
            ), secondary_y=True)
        else:
            fig.add_trace(go.Scatter(
                x=df_y['plot_date'], y=df_y[m2_col], name=f"{y} {m2_lab}",
                line=dict(color=color_map.get(y, '#ff7f0e'), dash='dash', width=2),
                customdata=df_y['hover_date'], hovertemplate="%{y:.1f}"
            ), secondary_y=True)

    # --- 5. ДИЗАЙН ---
    fig.update_layout(
        hovermode="x unified", barmode='group', height=600,
        template="simple_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    
    fig.update_yaxes(title_text=m1_lab, range=range1, secondary_y=False, 
                     showgrid=True, gridcolor='rgba(0,0,0,0.1)', zeroline=True, zerolinewidth=2)
    fig.update_yaxes(title_text=m2_lab, range=range2, secondary_y=True, 
                     showgrid=False, zeroline=True, zerolinewidth=2)
    
    st.plotly_chart(fig, use_container_width=True)