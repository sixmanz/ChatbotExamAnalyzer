# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time


# --- Modules ---
import src.styles as shadcn_style
from src.localization import t
from src.utils import (
    extract_text_from_pdf, 
    extract_text_from_docx, 
    check_bloom_criteria, 
    export_to_excel, 
    save_analysis_history,
    create_error_response,
    get_text_color_for_bloom, # Helper for UI
    get_bloom_color
)
from src.analysis import (
    extract_questions, 
    analyze_question, 
    AI_PROVIDERS, 
    DEFAULT_PROVIDER, 
    DEFAULT_MODEL_NAME,
    improve_question_with_ai,
    generate_exam_with_ai
)
from src.ui import (
    render_hero_section, 
    render_input_studio, 
    render_dashboard_overview, 
    render_detailed_results, 
    render_history_sidebar_v2,
    render_user_manual
)

# --- 2. Setup Page ---
st.set_page_config(
    page_title="AI Exam Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2.1 Load Custom Styles (Design Overhaul) ---
from src.styles import load_custom_css
load_custom_css()



# --- 2. Session State ---
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'question_texts' not in st.session_state: st.session_state.question_texts = []
if 'custom_prompt' not in st.session_state: st.session_state.custom_prompt = ""
if 'selected_provider' not in st.session_state: st.session_state.selected_provider = DEFAULT_PROVIDER
if 'selected_model' not in st.session_state: st.session_state.selected_model = DEFAULT_MODEL_NAME
if 'language' not in st.session_state: st.session_state.language = 'th'
if 'last_uploaded_file_name' not in st.session_state: st.session_state.last_uploaded_file_name = ""

# --- 3. Main Logic ---

# 3.1 Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6134/6134346.png", width=64)
    st.markdown(f"### {t('sidebar_title')}")
    
    # Check API Status
    from src.analysis import GEMINI_AVAILABLE # Import here to check status
    if GEMINI_AVAILABLE:
        st.caption(t('ai_connected'))
    else:
        st.error(t('ai_not_connected'))
    
    st.caption(f"{t('model_used')}: `{st.session_state.selected_model}`")
    
    st.markdown("---")
    render_history_sidebar_v2()
    
    st.markdown("---")
    st.caption("พัฒนาโดย:")
    st.markdown("**ตะวัน งามวงค์**")
    st.markdown("**เปรมปรีดิ์ กุลบุตร**")

# 3.2 Main Content
render_hero_section()
render_user_manual()

# 3.3 Logic for Analysis
def process_upload_and_analyze():
    """Callback for Start Analysis Button"""
    uploaded_file = st.session_state.get('file_uploader_widget')
    if not uploaded_file: return

    # --- Fast & Simple UI ---
    
    # A. Extract Text & Questions (One-Step)
    questions = st.session_state.get('question_texts')
    
    if questions:
        st.success(f"⚡ ใช้ข้อมูลทีสกัดไว้แล้ว ({len(questions)} ข้อ)")
    else:
        with st.spinner("🚀 กำลังแกะข้อสอบ..."):
            text = ""
            try:
                if uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type == "text/plain":
                    text = str(uploaded_file.read(), "utf-8")
                elif "wordprocessingml" in uploaded_file.type: # DOCX
                    text = extract_text_from_docx(uploaded_file)
            except Exception as e:
                st.error(f"{t('file_read_error')} {e}")
                return

            questions = extract_questions(text)
            
            if not questions:
                st.error(t('no_questions_found'))
                return
                
        st.session_state.question_texts = questions
        st.success(f"✅ พบ {len(questions)} ข้อ! กำลังเริ่มวิเคราะห์...")
    time.sleep(0.5) # Short pause for eye-candy
    
    # C. Analyze Each Question
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, q_text in enumerate(questions):
        status_text.caption(f"🤖 วิเคราะห์ข้อ {i+1}/{len(questions)}...")
        
        analysis = analyze_question(q_text, i+1)
        
        if not analysis:
            analysis = create_error_response("Analysis returned None")
            
        results.append(analysis)
        progress_bar.progress((i + 1) / len(questions))
    
    st.session_state.analysis_results = results
    
    # D. Save History
    summary_text = f"Analyzed {len(questions)} questions using {st.session_state.selected_provider}"
    save_analysis_history(uploaded_file.name, results, summary_text)
    
    status_text.empty()
    st.toast(t('analysis_complete'), icon="🎉")
    st.rerun()
    
    st.toast(t('analysis_complete'), icon="🎉")
    time.sleep(1)
    st.rerun()

# 3.4 Render Input Section
uploaded_file = render_input_studio(process_upload_and_analyze)

# 3.5 Render Results Section
if st.session_state.analysis_results:
    st.markdown(f"### {t('step3_title')}")
    
    # Prepare Data
    df = pd.DataFrame(st.session_state.analysis_results)
    
    # --- Fix: Rename Columns for UI Compatibility ---
    # Add 'Question Number' (Thai)
    df['ข้อที่'] = range(1, len(df) + 1)
    
    # Map Boolean Quality to Thai String
    df['คุณภาพข้อสอบ'] = df['is_good_question'].apply(lambda x: "✅ ดี" if x else "⚠️ ปรับปรุง")
    
    # Rename other columns to match UI expectation
    df = df.rename(columns={
        'bloom_level': 'ระดับความคิด',
        'improvement_suggestion': 'ข้อเสนอแนะ',
        'difficulty': 'ความยาก',
        'curriculum_standard': 'มาตรฐาน',
        'correct_option': 'คำตอบ'
    })

    bloom_check = check_bloom_criteria(st.session_state.analysis_results)
    
    # Calculate Summary Stats
    total = len(st.session_state.analysis_results)
    good = df[df['is_good_question'] == True].shape[0]
    bad = total - good
    
    summary_data = {
        "สถิติโดยรวม": {
            "จำนวนข้อสอบทั้งหมด": f"{total} ข้อ",
            "ข้อสอบ **ดี** (ใช้ได้เลย)": f"{good} ข้อ ({int(good/total*100)}%)" if total else "0",
            "ข้อสอบ **ต้องปรับปรุง**": f"{bad} ข้อ ({int(bad/total*100)}%)" if total else "0"
        }
    }
    
    # Tabs
    tab1, tab2 = st.tabs([f"📊 {t('tab_summary')}", f"📝 {t('tab_details')}"])
    
    with tab1:
        render_dashboard_overview(summary_data, bloom_check)
        render_detailed_results(st.session_state.analysis_results, bloom_check, summary_data, df)
        
        # Export Buttons
        col_ex1, col_ex2 = st.columns(2)
        
        # Excel
        excel_data = export_to_excel(st.session_state.analysis_results)
        if excel_data:
            with col_ex1:
                st.download_button(
                    label="📊 Download Excel Report",
                    data=excel_data,
                    file_name="exam_analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
        # Word
        from src.utils import export_to_word
        word_data = export_to_word(st.session_state.analysis_results)
        if word_data:
            with col_ex2:
                st.download_button(
                    label="📄 Download Word Report",
                    data=word_data,
                    file_name="exam_analysis_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    with tab2:
        st.markdown(f"#### {t('deep_dive_title')}")
        
        for idx, row in df.iterrows():
            q_num = row.get('ข้อที่', idx+1) # Fallback if 'ข้อที่' missing in sanitize? sanitize doesn't add it?
            # Wait, sanitize doesn't return 'ข้อที่'. app.py logic added it?
            # In old app.py: "ข้อที่": idx+1 was added when creating DF for table.
            # But here `row` comes from `st.session_state.analysis_results` which is list of dicts.
            # `df` was created from `st.session_state.analysis_results`.
            # If `analysis_results` pure dicts don't have 'ข้อที่', then df won't unless added.
            # Actually I used `df` in render_detailed_results which assumes columns.
            # Let's check `export_to_excel` in `utils.py` -> it iterates and adds index manually.
            # So `analysis_results` items DO NOT have 'ข้อที่'.
            # I should use `idx+1` for question number.
            
            with st.expander(f"Q{idx+1}: {row.get('bloom_level', 'N/A')} ({row.get('difficulty', 'N/A')})", expanded=False):
                col_q, col_a = st.columns([1.5, 1])
                
                with col_q:
                    # Show Original Question text if available
                    if idx < len(st.session_state.question_texts):
                        st.markdown(f"**{t('full_question')}**")
                        st.info(st.session_state.question_texts[idx])
                    
                    st.markdown(f"**{t('bloom_reason')}**")
                    st.write(row.get('reasoning', '-'))
                    
                    st.markdown(f"**{t('improvement_suggestion')}**")
                    if row.get('is_good_question'):
                        st.success(row.get('improvement_suggestion'))
                        
                        # Save to Question Bank Button
                        from src.database import add_to_question_bank
                        if st.button(f"💾 Save Q{idx+1} to Bank", key=f"save_bank_{idx}"):
                            orig_q = st.session_state.question_texts[idx] if idx < len(st.session_state.question_texts) else ""
                            add_to_question_bank(orig_q, row.to_dict(), "", st.session_state.get('last_uploaded_file_name', ''))
                            st.toast(f"✅ Q{idx+1} saved to Question Bank!", icon="📚")
                    else:
                        st.error(row.get('improvement_suggestion'))
                        
                        # Auto-Fix Feature
                        if st.button(f"{t('auto_fix_btn')} (Q{idx+1})", key=f"fix_{idx}"):
                             with st.spinner("AI is rewriting the question..."):
                                 orig_q = st.session_state.question_texts[idx] if idx < len(st.session_state.question_texts) else ""
                                 new_q, err = improve_question_with_ai(orig_q, row.get('improvement_suggestion'))
                                 if new_q:
                                     st.markdown("##### ✨ Question (Improved):")
                                     st.code(new_q, language='text')
                                 else:
                                     st.error(err)

                with col_a:
                     st.markdown(f"**{t('correct_analysis')}** ({row.get('correct_option', '?')})")
                     st.write(row.get('correct_option_analysis', '-'))
                     
                     st.markdown(f"**{t('distractor_analysis')}**")
                     st.write(row.get('distractor_analysis', '-'))