import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import apply_style, get_metrics_dict

def show(df_chart, color_map):
    st.subheader("🌡️ Аналіз температур вегетації")
    
    # 1. ПРАВИЛЬНА ТЕРМІНОЛОГІЯ
    m_dict = get_metrics_dict()
    m_name = st.radio(
        "Оберіть показник для аналізу:", 
        ["GDD (Ефективні Т > 10)", "Сума Т (якщо Т > 0)", "Сума Т (якщо Т > 10)"], 
        horizontal=True
    )
    
    # Сортування легенди
    df_chart = df_chart.sort_values(['year_str', 'plot_date'])
    years_ordered = sorted(df_chart['year_str'].unique())
    
    # Фільтр для накопичення (з 14/05)
    df_acc = df_chart[(df_chart['month'] > 5) | ((df_chart['month'] == 5) & (df_chart['day'] >= 14))].copy()

    # --- ГРАФІК 1: НАКОПИЧЕННЯ (GDD або Суми) ---
    fig_acc = px.line(
        df_acc, 
        x='plot_date', 
        y=m_dict[m_name], 
        color='year_str', 
        color_discrete_map=color_map,
        category_orders={"year_str": years_ordered},
        custom_data=['hover_date'],
        title=f"Накопичення: {m_name} (з 14/05)"
    )

    # Додаємо лінію середнього (Норма)
    metric_col = m_dict[m_name]
    avg_col = f"Avg_{metric_col}"
    if avg_col in df_acc.columns:
        df_avg_acc = df_acc[df_acc['year_str'] == df_acc['year_str'].unique()[0]]
        fig_acc.add_trace(go.Scatter(
            x=df_avg_acc['plot_date'],
            y=df_avg_acc[avg_col],
            name='Середнє (норма)',
            line=dict(color='black', width=3, dash='dash'),
            hovertemplate="Норма: %{y:.0f}"
        ))

    fig_acc.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Накопичено: %{y:.0f}')
    fig_acc.update_layout(hovermode="x unified")
    fig_acc.update_xaxes(tickformat="%d-%b", title=None)
    st.plotly_chart(apply_style(fig_acc), use_container_width=True)
    
    st.divider()

    # --- ГРАФІК 2: ЩОДЕННА ДИНАМІКА (ВЕСЬ РІК) ---
    st.subheader("❄️ Щоденна динаміка температур (Весь рік)")
    
    temp_mode = st.radio(
        "Показник дня:", 
        ["Середня Т", "Максимальна Т", "Мінімальна Т"], 
        horizontal=True
    )
    
    mode_map = {"Середня Т": "mean", "Максимальна Т": "max", "Мінімальна Т": "min"}
    target_col = mode_map[temp_mode]

    fig_daily = px.line(
        df_chart, 
        x='plot_date', 
        y=target_col, 
        color='year_str', 
        color_discrete_map=color_map,
        category_orders={"year_str": years_ordered},
        custom_data=['hover_date']
    )
    
    fig_daily.add_hline(y=-1, line_dash="dash", line_color="red", annotation_text="-1°C (Заморозок)")
    fig_daily.add_hline(y=0, line_color="gray", opacity=0.5)

    # Додаємо лінію середнього дня
    avg_daily_col = f"Avg_{target_col}"
    if avg_daily_col in df_chart.columns:
        df_avg_full = df_chart[df_chart['year_str'] == df_chart['year_str'].unique()[0]]
        fig_daily.add_trace(go.Scatter(
            x=df_avg_full['plot_date'],
            y=df_avg_full[avg_daily_col],
            name='Середнє (норма)',
            line=dict(color='black', width=2, dash='dot'),
            opacity=0.4,
            showlegend=True
        ))

    fig_daily.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Темп: %{y:.1f}°C')
    fig_daily.update_xaxes(tickformat="%d-%b", title=None)
    st.plotly_chart(apply_style(fig_daily), use_container_width=True)