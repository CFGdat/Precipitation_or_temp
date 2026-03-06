import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import apply_style, get_metrics_dict

def show(df_chart, color_map):
    st.subheader("🌡️ Аналіз температур вегетації")
    
    m_dict = get_metrics_dict()
    
    m_name = st.radio(
        "Оберіть показник для аналізу:", 
        [
            "GDD (Ефективні Т > 10)", 
            "Сума Т (якщо Т > 0)", 
            "Сума Т (якщо Т > 10)",
            "Теплові одиниці (Загальні)", 
            "CHU Соя (15.05 - мороз)"
        ], 
        horizontal=True
    )
    
    # Сортування легенди
    df_chart = df_chart.sort_values(['year_str', 'plot_date'])
    years_ordered = sorted(df_chart['year_str'].unique())
    
    # Фільтр для накопичення (з 14/05)
    df_acc = df_chart[(df_chart['month'] > 5) | ((df_chart['month'] == 5) & (df_chart['day'] >= 14))].copy()
    metric_col = m_dict.get(m_name, "Sum_T_active")

    # 🌟 НОВЕ: ВІЗУАЛЬНА ОБРІЗКА ГРАФІКА ДЛЯ CHU СОЯ
    if m_name == "CHU Соя (15.05 - мороз)":
        # 1. Обрізаємо лінії для кожного конкретного року
        for y in df_acc['year_str'].unique():
            # Шукаємо перший день з мінусом починаючи з 1 серпня
            frost_mask = (df_acc['year_str'] == y) & (df_acc['month'] >= 8) & (df_acc['min'] <= -1.0)
            if frost_mask.any():
                first_frost = df_acc[frost_mask]['plot_date'].min()
                # Заміняємо всі значення ПІСЛЯ морозу на NaN (графік перестане малюватись)
                df_acc.loc[(df_acc['year_str'] == y) & (df_acc['plot_date'] > first_frost), metric_col] = np.nan
        
        # 2. Обрізаємо чорну лінію середнього (Норми), якщо вона є
        avg_col = f"Avg_{metric_col}"
        if avg_col in df_acc.columns and 'Avg_min' in df_acc.columns:
            avg_frost_mask = (df_acc['month'] >= 8) & (df_acc['Avg_min'] <= -1.0)
            if avg_frost_mask.any():
                avg_frost = df_acc[avg_frost_mask]['plot_date'].min()
                df_acc.loc[df_acc['plot_date'] > avg_frost, avg_col] = np.nan

    # --- ГРАФІК 1: НАКОПИЧЕННЯ ---
    fig_acc = px.line(
        df_acc, 
        x='plot_date', 
        y=metric_col, 
        color='year_str', 
        color_discrete_map=color_map,
        category_orders={"year_str": years_ordered},
        custom_data=['hover_date'],
        title=f"Накопичення: {m_name} (з 14/05)"
    )

    # Додаємо лінію середнього (Норма)
    avg_col = f"Avg_{metric_col}"
    if avg_col in df_acc.columns:
        df_avg_acc = df_acc[df_acc['year_str'] == df_acc['year_str'].unique()[0]]
        fig_acc.add_trace(go.Scatter(
            x=df_avg_acc['plot_date'],
            y=df_avg_acc[avg_col],
            name='Середнє (норма)',
            line=dict(color='black', width=3, dash='dash'),
            hovertemplate="Норма: %{y:.0f}",
            connectgaps=False # Гарантує, що лінія не буде з'єднувати порожнечі
        ))

    fig_acc.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Накопичено: %{y:.0f}', connectgaps=False)
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
