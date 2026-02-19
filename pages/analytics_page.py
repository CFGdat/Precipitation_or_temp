import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from utils import get_metrics_dict

def show(df_chart, color_map):
    st.markdown("### 📊 Аналітичний модуль")
    
    tab_rain, tab_similarity = st.tabs(["🌧️ Аналіз дощових періодів", "🧬 Конструктор схожості років"])

    # Формування періодів (декад)
    if 'month' in df_chart.columns and 'decade' in df_chart.columns:
        df_chart['Період'] = df_chart['month'].astype(str).str.zfill(2) + "-" + df_chart['decade'].astype(str)
        df_chart = df_chart.sort_values(['year_str', 'plot_date'])
    
    # --- ВКЛАДКА 1: АНАЛІЗ ДОЩОВИХ ПЕРІОДІВ ---
    with tab_rain:
        if 'precipitation' in df_chart.columns and 'Період' in df_chart.columns:
            df_chart_risk = df_chart.copy()
            df_chart_risk['is_rainy_3mm'] = (df_chart_risk['precipitation'] > 3).astype(int)
            df_chart_risk['is_rainy_any'] = (df_chart_risk['precipitation'] > 0).astype(bool)
            
            all_periods = sorted(df_chart_risk['Період'].unique())
            
            # Оновлена функція з легендою
            def create_heatmap(df_pivot, title, colors, z_label):
                fig = px.imshow(
                    df_pivot, 
                    text_auto=".0f", 
                    aspect="auto", 
                    color_continuous_scale=colors,
                    labels=dict(x="Декада", y="Рік", color=z_label)
                )
                fig.update_layout(
                    title=title,
                    height=400, # Трохи збільшили висоту для кращого вигляду з легендою
                    margin=dict(t=50, b=10, l=0, r=50), # Додали відступ справа для шкали
                    coloraxis_showscale=True, # ПОВЕРНУЛИ ЛЕГЕНДУ
                    xaxis=dict(type='category', tickangle=-45)
                )
                return fig

            # 1. Сума опадів
            rain_sum_agg = df_chart_risk.groupby(['year_str', 'Період'])['precipitation'].sum().reset_index()
            rain_sum_pivot = rain_sum_agg.pivot(index='year_str', columns='Період', values='precipitation').fillna(0)[all_periods]
            st.plotly_chart(create_heatmap(rain_sum_pivot, "🌧️ Сума опадів по декадах (мм)", "Blues", "мм"), use_container_width=True)
            
            st.divider()
            
            # 2. Дні > 3 мм
            risk_3mm_agg = df_chart_risk.groupby(['year_str', 'Період'])['is_rainy_3mm'].sum().reset_index()
            risk_3mm_pivot = risk_3mm_agg.pivot(index='year_str', columns='Період', values='is_rainy_3mm').fillna(0)[all_periods]
            st.plotly_chart(create_heatmap(risk_3mm_pivot, "🚜 Дні з опадами понад 3 мм", "RdYlGn_r", "днів"), use_container_width=True)
            
            st.divider()
            
            # 3. Дощові дні всього
            total_rain_agg = df_chart_risk.groupby(['year_str', 'Період'])['is_rainy_any'].sum().reset_index()
            total_rain_pivot = total_rain_agg.pivot(index='year_str', columns='Період', values='is_rainy_any').fillna(0)[all_periods]
            st.plotly_chart(create_heatmap(total_rain_pivot, "☔ Загальна кількість дощових днів (>0)", "PuBu", "днів"), use_container_width=True)
            
            st.divider()
            
            # 4. Дні підряд
            def get_max_streak(s):
                return int(s.groupby((~s).cumsum()).sum().max()) if s.any() else 0
            streak_agg = df_chart_risk.groupby(['year_str', 'Період'])['is_rainy_any'].apply(get_max_streak).reset_index(name='streak')
            streak_pivot = streak_agg.pivot(index='year_str', columns='Період', values='streak').fillna(0)[all_periods]
            st.plotly_chart(create_heatmap(streak_pivot, "⛈️ Затяжні дощі (Макс. днів підряд)", "Oranges", "днів"), use_container_width=True)

        else:
            st.warning("Дані для аналізу опадів відсутні.")

    # --- ВКЛАДКА 2: КОНСТРУКТОР СХОЖОСТІ (БЕЗ ЗМІН) ---
    with tab_similarity:
        st.subheader("🧬 Пошук кліматично подібних років")
        m_dict = get_metrics_dict()
        inv_m_dict = {v: k for k, v in m_dict.items()}

        c1, c2 = st.columns([2, 1])
        with c1:
            selected_labels = st.multiselect("1. Показники:", options=list(m_dict.keys()), default=["GDD (Ефективні Т > 10)", "Накопичені опади"])
            sim_params_keys = [m_dict[label] for label in selected_labels]
        with c2:
            years_list = sorted(df_chart['year_str'].dropna().unique(), reverse=True)
            ref_year = st.selectbox("2. Еталон:", years_list, index=years_list.index('2025') if '2025' in years_list else 0)

        if selected_labels and not df_chart.empty:
            df_years = df_chart.groupby('year_str')[sim_params_keys].max()
            if ref_year in df_years.index:
                ref_vals = df_years.loc[ref_year]
                def calc_sim(row):
                    diffs = []
                    for col in sim_params_keys:
                        val, target = row[col], ref_vals[col]
                        if pd.isna(val) or pd.isna(target): continue
                        d = abs(val - target) / abs(target) if target != 0 else (0 if val == 0 else 1)
                        diffs.append(min(d, 1))
                    return (1 - np.mean(diffs)) * 100 if diffs else 0

                df_years['Схожість %'] = df_years.apply(calc_sim, axis=1)
                df_disp = df_years.rename(columns=inv_m_dict).reset_index().sort_values('Схожість %', ascending=False)
                
                col_t, col_c = st.columns([1, 1])
                with col_t:
                    st.dataframe(df_disp.style.background_gradient(subset=['Схожість %'], cmap="Greens").format({"Схожість %": "{:.2f}%"} | {l: "{:.1f}" for l in selected_labels}), use_container_width=True, height=450)
                with col_c:
                    fig_sim = px.bar(df_disp, x='year_str', y='Схожість %', color='Схожість %', color_continuous_scale='Greens')
                    fig_sim.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                    fig_sim.update_layout(yaxis=dict(range=[0, 115]), xaxis=dict(type='category'), height=450)
                    st.plotly_chart(fig_sim, use_container_width=True)