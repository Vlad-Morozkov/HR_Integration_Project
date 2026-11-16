import streamlit as st

def show_about_page(t: dict):
    """
    Отображает страницу 'О проекте'.
    Принимает словарь переводов t.
    """
    st.header(t.get("about", "About Project"))
    
    st.markdown(f"### {t.get('about_title', 'HR Integration System')}")
    st.write(t.get('about_desc', 'A full-stack application...'))
    
    st.divider()
    
    # --- БЛОК: ФИЧИ И ИНТЕГРАЦИИ ---
    st.subheader(t.get("about_features_title", "Key Features & Integrations"))
    
    col_feat1, col_feat2 = st.columns(2)
    with col_feat1:
        st.info(t.get("about_feat_i18n", "..."))
        st.success(t.get("about_feat_email", "..."))
        
    with col_feat2:
        st.warning(t.get("about_feat_demo", "..."))
        st.info(t.get("about_feat_design", "..."))
        
    st.divider()

    # --- БЛОК: АРХИТЕКТУРА И ТЕСТИРОВАНИЕ ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(t.get("about_arch_title", "🛠 Architecture Decisions"))
        st.markdown(t.get("about_arch_text", ""))
        
    with col2:
        st.subheader(t.get("about_test_title", "🧪 How to Test"))
        st.markdown(t.get("about_test_text", ""))
        
    st.divider()
    
    # --- БЛОК: ТЕХНОЛОГИЧЕСКИЙ СТЕК ---
    st.subheader(t.get("stack", "💻 Technology stack"))
    
    st.markdown("""
    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
        <span style="background: #e3f2fd; padding: 5px 10px; border-radius: 5px; color: #0d47a1; font-weight: bold;">FastAPI</span>
        <span style="background: #e8f5e9; padding: 5px 10px; border-radius: 5px; color: #1b5e20; font-weight: bold;">Streamlit</span>
        <span style="background: #fff3e0; padding: 5px 10px; border-radius: 5px; color: #e65100; font-weight: bold;">SQLAlchemy</span>
        <span style="background: #f3e5f5; padding: 5px 10px; border-radius: 5px; color: #4a148c; font-weight: bold;">Pydantic</span>
        <span style="background: #ffebee; padding: 5px 10px; border-radius: 5px; color: #b71c1c; font-weight: bold;">Cal.com API</span>
        <span style="background: #fce4ec; padding: 5px 10px; border-radius: 5px; color: #880e4f; font-weight: bold;">Google SMTP</span>
        <span style="background: #336791; padding: 5px 10px; border-radius: 5px; color: #ffffff; font-weight: bold;">PostgreSQL</span>
        <span style="background: #00e599; padding: 5px 10px; border-radius: 5px; color: #000000; font-weight: bold;">Neon</span>
        <span style="background: #eceff1; padding: 5px 10px; border-radius: 5px; color: #263238; font-weight: bold;">Vercel</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # --- БЛОК: УПОМИНАНИЕ ИИ ---
    st.info(t.get("about_ai_mention", "Pair Programming with AI..."))
    
    st.caption("Developed as a portfolio project for System Analyst role. 2026.")