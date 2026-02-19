import streamlit as st
import pandas as pd
import utils

def show(df_chart, sel_years, sel_cluster, sel_block, sel_culture):
    st.subheader("📋 Таблиці даних")
    
    if df_chart.empty:
        st.info("Немає даних для формування таблиць.")
        return

    valid_metrics = list(utils.get_metrics_dict().values())
    avg_cols = [f"Avg_{m}" for m in valid_metrics if f"Avg_{m}" in df_chart.columns]
    
    # --- 1. АГРЕГОВАНІ ДАНІ (Оптимізовано для списків) ---
    st.markdown("#### 1. Агреговані дані (Середнє по вибірці)")
    df_show = df_chart[['year_str', 'hover_date'] + valid_metrics + avg_cols].copy()
    
    # Перетворюємо списки вибору в один рядок тексту, щоб Pandas не видавав ValueError
    cluster_txt = ", ".join(map(str, sel_cluster)) if isinstance(sel_cluster, list) else str(sel_cluster)
    block_txt = ", ".join(map(str, sel_block)) if isinstance(sel_block, list) else str(sel_block)
    culture_txt = ", ".join(map(str, sel_culture)) if isinstance(sel_culture, list) else str(sel_culture)
    
    df_show.insert(0, 'Кластер', cluster_txt)
    df_show.insert(1, 'Блок', block_txt)
    df_show.insert(2, 'Культура', culture_txt)
    
    rename_dict = {f"Avg_{m}": f"Сер. {m}" for m in valid_metrics}
    df_show = df_show.rename(columns={'year_str': 'Рік', 'hover_date': 'Дата'} | rename_dict)
    
    st.dataframe(
        df_show.style.format("{:.1f}", subset=[c for c in df_show.columns if c not in ['Рік', 'Дата', 'Кластер', 'Блок', 'Культура']]), 
        use_container_width=True
    )
    
    st.download_button("📥 Скачати агреговані дані (CSV)", df_show.to_csv(index=False).encode('utf-8'), "agro_report_agg.csv", "text/csv")

    st.divider()

    # --- 2. ДЕТАЛЬНІ ДАНІ (З фільтрацією списків .isin()) ---
    st.markdown("#### 2. Детальні дані (Рівень окремих полів)")
    st.info("Натисніть кнопку, щоб завантажити детальну розбивку по полях.")
    
    if st.button("🚀 Завантажити дані по полях"):
        with st.spinner("Завантаження WEB_FINAL_READY.parquet..."):
            df_raw_full = utils.load_raw_data()
            
            if df_raw_full.empty:
                st.error("Файл з детальними даними не знайдено.")
                return

            # Фільтрація за списками (використовуємо .isin)
            mask = df_raw_full['year'].isin(sel_years)
            
            if "Всі" not in sel_cluster and sel_cluster:
                mask &= (df_raw_full['Cluster'].isin(sel_cluster))
            if "Всі" not in sel_block and sel_block:
                mask &= (df_raw_full['Block'].isin(sel_block))
            if "Всі" not in sel_culture and sel_culture:
                mask &= (df_raw_full['Culture'].isin(sel_culture))
            
            df_detailed = df_raw_full[mask].copy()

            if df_detailed.empty:
                st.warning("За обраними фільтрами в детальному файлі нічого не знайдено.")
                return

            # Пріоритетний порядок колонок
            priority_cols = ['date', 'location', 'Cluster', 'Block', 'Culture']
            exist_priority = [c for c in priority_cols if c in df_detailed.columns]
            exist_metrics = [c for c in valid_metrics if c in df_detailed.columns]
            other_cols = [c for c in df_detailed.columns if c not in exist_priority and c not in exist_metrics]
            
            final_order = exist_priority + exist_metrics + other_cols
            
            st.success(f"Дані завантажено. Всього записів: {len(df_detailed)}")
            st.dataframe(df_detailed[final_order].head(2000), use_container_width=True)
            
            csv = df_detailed[final_order].to_csv(index=False).encode('utf-8')
            st.download_button("📥 Скачати ПОВНИЙ звіт (CSV)", csv, "detailed_fields.csv", "text/csv")