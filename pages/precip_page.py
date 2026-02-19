import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils import apply_style, get_metrics_dict

def show(df_chart, color_map):
    st.subheader("💧 Вологозабезпечення")

    m_dict = get_metrics_dict()
    acc_col = m_dict.get('Накопичені опади', 'Sum_Precipitation')
    daily_col = m_dict.get('Щоденні опади', 'precipitation')
    avg_acc_col = f"Avg_{acc_col}"

    # 1. СОРТУВАННЯ ДАНИХ
    df_chart = df_chart.sort_values(['year_str', 'plot_date'])
    years_ordered = sorted(df_chart['year_str'].unique())

    # --- ГРАФІК 1: НАКОПИЧЕНІ ОПАДИ ---
    fig_acc = px.line(
        df_chart, x='plot_date', y=acc_col, color='year_str',
        color_discrete_map=color_map,
        category_orders={"year_str": years_ordered}, 
        title="Накопичена сума опадів (мм)",
        labels={acc_col: 'Опади, мм', 'plot_date': 'Дата', 'year_str': 'Рік'}
    )

    if avg_acc_col in df_chart.columns:
        first_year = df_chart['year_str'].unique()[0]
        df_avg_line = df_chart[df_chart['year_str'] == first_year]
        fig_acc.add_trace(go.Scatter(
            x=df_avg_line['plot_date'], y=df_avg_line[avg_acc_col],
            name='Середнє по вибірці',
            line=dict(color='black', width=3, dash='dash'),
            hovertemplate="Середнє: %{y:.1f} мм"
        ))

    fig_acc = apply_style(fig_acc)
    fig_acc.update_xaxes(tickformat="%d-%b")
    st.plotly_chart(fig_acc, use_container_width=True)

    st.divider()

    # --- ГРАФІК 2: ІНТЕНСИВНІСТЬ ОПАДІВ ---
    st.subheader("🌧️ Інтенсивність щоденних опадів")
    
    # ПОВЕРНУТО ДЕФОЛТНИЙ ПЕРІОД (9, 9)
    month_range = st.slider(
        "Оберіть діапазон місяців для аналізу інтенсивності:", 
        1, 12, (9, 9), 
        help="Перетягніть повзунки, щоб змінити період на графіку нижче"
    )
    
    df_daily = df_chart[df_chart['month'].between(month_range[0], month_range[1])]
    
    if not df_daily.empty:
        fig_daily = px.bar(
            df_daily, x='plot_date', y=daily_col, color='year_str',
            color_discrete_map=color_map,
            category_orders={"year_str": years_ordered},
            barmode='group',
            title=f"Щоденні опади (Місяці: {month_range[0]} - {month_range[1]})",
            labels={daily_col: 'мм', 'plot_date': 'Дата', 'year_str': 'Рік'}
        )
        
        fig_daily = apply_style(fig_daily)
        fig_daily.update_xaxes(tickformat="%d-%b")
        st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.warning("Немає даних за вибраний період місяців.")