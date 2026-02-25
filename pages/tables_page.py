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

    # ── 1. АГРЕГОВАНІ ДАНІ ───────────────────────────────────────────────────
    st.markdown("#### 1. Агреговані дані (Середнє по вибірці)")
    df_show = df_chart[['year_str', 'hover_date'] + valid_metrics + avg_cols].copy()

    cluster_txt = ", ".join(map(str, sel_cluster)) if isinstance(sel_cluster, list) else str(sel_cluster)
    block_txt   = ", ".join(map(str, sel_block))   if isinstance(sel_block,   list) else str(sel_block)
    culture_txt = ", ".join(map(str, sel_culture)) if isinstance(sel_culture, list) else str(sel_culture)

    df_show.insert(0, 'Кластер',  cluster_txt)
    df_show.insert(1, 'Блок',     block_txt)
    df_show.insert(2, 'Культура', culture_txt)

    rename_dict = {f"Avg_{m}": f"Сер. {m}" for m in valid_metrics}
    df_show = df_show.rename(columns={'year_str': 'Рік', 'hover_date': 'Дата'} | rename_dict)

    st.dataframe(
        df_show.style.format(
            "{:.1f}",
            subset=[c for c in df_show.columns if c not in ['Рік', 'Дата', 'Кластер', 'Блок', 'Культура']]
        ),
        use_container_width=True
    )
    st.download_button(
        "📥 Скачати агреговані дані (CSV)",
        df_show.to_csv(index=False).encode('utf-8'),
        "agro_report_agg.csv", "text/csv"
    )

    st.divider()

    # ── 2. ЗВЕДЕНІ ДАНІ ПО ПОЛЯХ ─────────────────────────────────────────────
    st.markdown("#### 2. Зведені дані по полях (Поле + Рік)")

    # Миттєво завантажуємо вже готовий легкий файл
    df_summary = utils.load_field_summary()

    if df_summary.empty:
        return

    # ── ФІЛЬТРАЦІЯ ──
    # У підготовленому файлі ми перейменували 'year' на 'Рік'
    if 'Рік' in df_summary.columns and sel_years:
        # Безпечне порівняння, незалежно від того чи це числа, чи рядки
        df_summary = df_summary[df_summary['Рік'].astype(str).isin([str(y) for y in sel_years])]
        
    if "Всі" not in sel_cluster and sel_cluster and 'Cluster' in df_summary.columns:
        df_summary = df_summary[df_summary['Cluster'].isin(sel_cluster)]
        
    if "Всі" not in sel_block and sel_block and 'Block' in df_summary.columns:
        df_summary = df_summary[df_summary['Block'].isin(sel_block)]
        
    if "Всі" not in sel_culture and sel_culture and 'Culture' in df_summary.columns:
        df_summary = df_summary[df_summary['Culture'].isin(sel_culture)]

    if df_summary.empty:
        st.warning("За обраними фільтрами нічого не знайдено.")
    else:
        _render_summary(df_summary)


# ─────────────────────────────────────────────────────────────────────────────
# ВНУТРІШНІ ФУНКЦІЇ
# ─────────────────────────────────────────────────────────────────────────────

def _render_summary(df_summary):
    """Відображає готову зведену таблицю та кнопку завантаження."""
    frost_cols   = [c for c in df_summary.columns if 'мороз' in c.lower()]
    priority     = ['Поле', 'Cluster', 'Block', 'Culture', 'Рік']
    
    exist_pri    = [c for c in priority if c in df_summary.columns]
    other        = [c for c in df_summary.columns if c not in exist_pri and c not in frost_cols]
    final_order  = exist_pri + other + frost_cols

    # Вибудовуємо правильний порядок колонок
    df_display = df_summary[[c for c in final_order if c in df_summary.columns]]

    st.success(f"Знайдено {len(df_display)} записів по полях.")
    st.dataframe(df_display, use_container_width=True, height=500)

    # Кнопка завантаження
    csv = df_display.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 Скачати зведені дані по полях (CSV)",
        csv,
        "fields_summary.csv",
        "text/csv"
    )
