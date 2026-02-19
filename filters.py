import streamlit as st

def render_sidebar(df):
    st.sidebar.header("🔍 Налаштування")

    # --- 1. КНОПКА СКИНУТИ ВСІ ФІЛЬТРИ ---
    if st.sidebar.button("🗑️ Скинути всі фільтри", use_container_width=True):
        # Повертаємо всі стани до дефолтного "Всі"
        st.session_state.sel_year_state = ["Всі"]
        st.session_state.sel_cluster_state = ["Всі"]
        st.session_state.sel_block_state = ["Всі"]
        st.session_state.sel_culture_state = ["Всі"]
        st.rerun()

    # --- 2. УНІВЕРСАЛЬНИЙ ОБРОБНИК (CALLBACK) ---
    def sync_multiselect(key):
        """Логіка перемикання 'Всі' vs конкретика для будь-якого фільтра"""
        current = st.session_state[key]
        if not current:
            st.session_state[key] = ["Всі"]
        elif len(current) > 1:
            if "Всі" in current:
                # Якщо натиснули "Всі" останнім - скидаємо все інше
                if current[-1] == "Всі":
                    st.session_state[key] = ["Всі"]
                # Якщо було "Всі", а вибрали рік/кластер - прибираємо "Всі"
                else:
                    st.session_state[key] = [x for x in current if x != "Всі"]

    # --- 3. РОКИ (Тепер теж "Розумний") ---
    all_years_opts = sorted(df['year'].unique().tolist(), reverse=True)
    if "sel_year_state" not in st.session_state:
        st.session_state.sel_year_state = ["Всі"]

    st.sidebar.multiselect(
        "Оберіть роки:", 
        options=["Всі"] + all_years_opts,
        key="sel_year_state",
        on_change=sync_multiselect,
        args=("sel_year_state",)
    )
    
    # Визначаємо фінальний список років для фільтрації
    if "Всі" in st.session_state.sel_year_state:
        sel_years = all_years_opts
    else:
        sel_years = st.session_state.sel_year_state
        
    df_f = df[df['year'].isin(sel_years)]

    # --- 4. КЛАСТЕР ---
    cluster_opts = sorted(df_f['Cluster'].unique().tolist())
    if "sel_cluster_state" not in st.session_state:
        st.session_state.sel_cluster_state = ["Всі"]
        
    st.sidebar.multiselect(
        "Кластер:", options=["Всі"] + cluster_opts, 
        key="sel_cluster_state", on_change=sync_multiselect, args=("sel_cluster_state",)
    )
    sel_cluster = st.session_state.sel_cluster_state
    if "Всі" not in sel_cluster:
        df_f = df_f[df_f['Cluster'].isin(sel_cluster)]

    # --- 5. БЛОК ---
    block_opts = sorted(df_f['Block'].unique().tolist())
    if "sel_block_state" not in st.session_state:
        st.session_state.sel_block_state = ["Всі"]
        
    st.sidebar.multiselect(
        "Блок:", options=["Всі"] + block_opts, 
        key="sel_block_state", on_change=sync_multiselect, args=("sel_block_state",)
    )
    sel_block = st.session_state.sel_block_state
    if "Всі" not in sel_block:
        df_f = df_f[df_f['Block'].isin(sel_block)]

    # --- 6. КУЛЬТУРА ---
    culture_opts = sorted(df_f['Culture'].unique().tolist())
    if "sel_culture_state" not in st.session_state:
        st.session_state.sel_culture_state = ["Всі"]
        
    st.sidebar.multiselect(
        "Культура:", options=["Всі"] + culture_opts, 
        key="sel_culture_state", on_change=sync_multiselect, args=("sel_culture_state",)
    )
    sel_culture = st.session_state.sel_culture_state
    if "Всі" not in sel_culture:
        df_f = df_f[df_f['Culture'].isin(sel_culture)]

    return df_f, sel_years, sel_cluster, sel_block, sel_culture