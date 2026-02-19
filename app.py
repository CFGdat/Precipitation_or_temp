import streamlit as st
import pandas as pd

# 1. ОСНОВНА КОНФІГУРАЦІЯ
st.set_page_config(
    page_title="Agro Analytics Pro+", 
    layout="wide", 
    initial_sidebar_state="collapsed" 
)

# 2. CSS ДЛЯ ПРИХОВУВАННЯ ТЕХНІЧНИХ ЕЛЕМЕНТІВ ТА СТИЛІЗАЦІЇ
st.markdown("""
    <style>
        /* Ховаємо навігацію та сайдбар до моменту входу */
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none; }
        
        .block-container { padding-top: 1.5rem !important; }
        
        /* Стиль статусної стрічки (Status Ribbon) */
        .status-ribbon {
            background-color: #f0f2f6;
            padding: 8px 18px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 15px;
            border: 1px solid #d1d5da;
        }
        .tag {
            background: white;
            border: 1px solid #d1d5da;
            padding: 1px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            color: #24292e;
            white-space: nowrap;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. БЛОК БЕЗПЕКИ (АВТОРИЗАЦІЯ) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🚜 Agro Analytics Access")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input("Введіть пароль:", type="password", key="password_input")
            if st.button("Увійти", use_container_width=True):
                if st.session_state["password_input"] == st.secrets["auth"]["password"]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("😕 Невірний пароль.")
        return False
    return True

if not check_password():
    st.stop()

# Показуємо сайдбар тільки після успішного входу
st.markdown("<style>section[data-testid='stSidebar'] { display: flex !important; }</style>", unsafe_allow_html=True)

# --- 4. ЗАВАНТАЖЕННЯ МОДУЛІВ ТА ДАНИХ ---
import utils
import filters
from pages import temp_page, precip_page, tables_page, constructor_page, analytics_page

df_full = utils.load_data()
color_map = utils.get_colors(df_full)

# --- 5. САЙДБАР (ФІЛЬТРИ) ---
df_f, sel_years, sel_cluster, sel_block, sel_culture = filters.render_sidebar(df_full)

if df_f.empty:
    st.title("🚜 Agro Analytics")
    st.warning("⚠️ Оберіть параметри у фільтрах сайдбару.")
    st.stop()

# --- 6. ПІДГОТОВКА ДАНИХ ТА СИНХРОНІЗАЦІЯ МЕТРИК ---
metrics_dict = utils.get_metrics_dict()
metrics = list(metrics_dict.values())

# Агрегація для графіків (Середнє по днях)
group_cols = ['year_str', 'plot_date', 'hover_date', 'month', 'day', 'decade']
df_chart = df_f.groupby(group_cols)[metrics + ['field_count']].mean().reset_index().sort_values('plot_date')

# Автоматичне створення колонок Норми (Avg_...) для всіх метрик
for m in metrics:
    if m in df_chart.columns:
        df_chart[f"Avg_{m}"] = df_chart.groupby('plot_date')[m].transform('mean')

# --- 7. КОНТРОЛЬНА ПАНЕЛЬ (STATUS RIBBON) ---
st.title("🚜 Agro Analytics")

# Математика масштабу (Поле-Рік)
daily_sum = df_f.groupby(['year', 'plot_date'])['field_count'].sum().reset_index()
yearly_max = daily_sum.groupby('year')['field_count'].max()
total_scale = int(yearly_max.sum())
avg_fields = int(yearly_max.mean())
num_years = len(sel_years)
tt_text = f"Масштаб аналізу: ~{avg_fields} полів × {num_years} років моніторингу (період до 2026 р.)."

active_c = ", ".join(sel_cluster) if "Всі" not in sel_cluster else "Всі кластери"
active_b = ", ".join(sel_block) if "Всі" not in sel_block else "Всі блоки"
active_cul = ", ".join(sel_culture) if "Всі" not in sel_culture else "Всі культури"

st.markdown(f"""
    <div class="status-ribbon">
        <div style="display: flex; flex-direction: column; line-height: 1.1;">
            <span style="font-size: 0.65rem; color: #586069; text-transform: uppercase; font-weight: 700;">
                📍 Локацій <span title="{tt_text}" style="cursor: help; color: #0366d6;">ⓘ</span>
            </span>
            <span style="font-size: 1.05rem; font-weight: 700; color: #24292e;">{total_scale:,}</span>
        </div>
        <div style="width: 1px; height: 22px; background-color: #d1d5da;"></div>
        <div style="display: flex; flex-direction: column; line-height: 1.1;">
            <span style="font-size: 0.65rem; color: #586069; text-transform: uppercase; font-weight: 700;">📅 Еталон</span>
            <span style="font-size: 1.05rem; font-weight: 700; color: #24292e;">{utils.ETALON_YEAR}</span>
        </div>
        <div style="width: 1px; height: 22px; background-color: #d1d5da;"></div>
        <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center;">
            <span style="font-size: 0.65rem; color: #586069; text-transform: uppercase; font-weight: 700;">🔍 ВИБРАНО:</span>
            <div class="tag">🏙️ {active_c}</div>
            <div class="tag">📦 {active_b}</div>
            <div class="tag">🌾 {active_cul}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 8. ТАБИ (ОСНОВНИЙ ІНТЕРФЕЙС) ---
tabs = st.tabs(["🌡️ Температури", "💧 Опади", "📋 Таблиці", "🛠️ Конструктор", "📊 Аналітика"])

with tabs[0]: temp_page.show(df_chart, color_map)
with tabs[1]: precip_page.show(df_chart, color_map)
with tabs[2]: tables_page.show(df_chart, sel_years, sel_cluster, sel_block, sel_culture) 
with tabs[3]: constructor_page.show(df_chart, color_map)

with tabs[4]: analytics_page.show(df_chart, color_map)

