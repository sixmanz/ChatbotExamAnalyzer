# -*- coding: utf-8 -*-
import os
import time
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime

# Internal Imports
from .localization import t, toggle_language
from .analysis import AI_PROVIDERS
from .utils import get_bloom_color, load_analysis_history, clear_all_history

def render_hero_section():
    """ส่วนหัวของแอพแบบ Minimalist Dashboard"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div style="padding-top: 1rem;">
            <h1 style="font-size: 1.8rem; font-weight: 700; margin-bottom: 0px; color: #1e293b; letter-spacing: -0.02em;">
                {t('app_title')}
            </h1>
            <p style="font-size: 1rem; color: #64748b; margin-top: 4px;">
                AI Exam Analysis Dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Mini Toolbar
        c1, c2 = st.columns([1, 2]) 
        with c1:
             st.button(
                t('language_btn'), 
                on_click=toggle_language,
                use_container_width=True,
                key='top_lang_toggle'
            )
        with c2:
             with st.popover(t('ai_config'), use_container_width=True):
                 st.caption("AI Provider & Model")
                 
                 provider_options = list(AI_PROVIDERS.keys())
                 current_idx = provider_options.index(st.session_state.selected_provider) if st.session_state.selected_provider in provider_options else 0
                 new_provider = st.selectbox(t('provider_label'), provider_options, index=current_idx, key='top_provider')
                 
                 if new_provider != st.session_state.selected_provider:
                    st.session_state.selected_provider = new_provider
                    first_model = list(AI_PROVIDERS[new_provider]["models"].keys())[0]
                    st.session_state.selected_model = first_model
                    st.session_state.analysis_results = None
                    st.rerun()
                    
                 model_options = list(AI_PROVIDERS[st.session_state.selected_provider]["models"].keys())
                 current_midx = model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0
                 new_model = st.selectbox(t('model_label'), model_options, index=current_midx, key='top_model')
                 
                 if new_model != st.session_state.selected_model:
                     st.session_state.selected_model = new_model
                     st.session_state.analysis_results = None
    
    st.markdown("---")

def render_user_manual():
    """Show User Manual"""
    with st.expander("&#128218; คู่มือสำหรับมือใหม่ (คลิกอ่าน)", expanded=False):
        st.markdown('''
        **1. เริ่มต้นใช้งาน &#128640;**
        - เลือกไฟล์ข้อสอบ (PDF, DOCX, TXT) จากเครื่อง
        - ระบบจะสกัดโจทย์ออกมาให้ตรวจสอบ
        
        **2. การเลือก AI (สำคัญ) &#129504;**
        - **Gemini**: ฉลาดที่สุด แต่อาจติด Limit (429)
        - **Groq**: เร็วมาก & ฟรี! (แนะนำเมื่อ Gemini เต็ม)
        - *เปลี่ยนได้ที่ "เลือก AI Provider" ด้านล่าง*
        ''')

def render_top_navigation():
    """Show Top Navigation Bar (Settings & Manual)"""
    pass # Integrated into render_hero_section now for cleaner UI

def render_history_sidebar_v2():
    """Show History in Sidebar"""
    history = load_analysis_history()
    
    if not history:
        st.info("ยังไม่มีประวัติ")
        return

    if st.button("🗑️ ล้างประวัติทั้งหมด", key="clear_hist_btn", use_container_width=True):
        try:
             clear_all_history()
             st.success("ล้างประวัติเรียบร้อย")
             time.sleep(1)
             st.rerun()
        except Exception as e:
             st.error(f"ล้างประวัติไม่สำเร็จ: {e}")

    for i, entry in enumerate(reversed(history)):
        timestamp = entry.get('timestamp', 'N/A')
        filename = entry.get('filename', 'Unknown')
        total = entry.get('total_questions', 0)
        good = entry.get('good_questions', 0)
        
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%d/%m %H:%M")
        except (ValueError, TypeError):
            time_str = timestamp

        with st.expander(f"📂 {filename}", expanded=False):
            st.caption(f"🕒 {time_str}")
            st.markdown(f"**จำนวน:** {total} ข้อ")
            st.markdown(f"**คุณภาพดี:** {good} ข้อ")
            
            # Use ID for loading if available (from DB), else fallback?
            # DB returns dict with 'id'
            exam_id = entry.get('id')
            
            if st.button("⚡ โหลดผลลัพธ์", key=f"hist_btn_{i}_{exam_id}", use_container_width=True):
                # Import here to avoid circular ref issue if top-level
                from .utils import load_exam_results
                
                # Load full results from DB
                loaded_results = load_exam_results(exam_id)
                if loaded_results:
                    st.session_state.analysis_results = loaded_results
                    st.session_state.question_texts = []
                    st.success(f"โหลด: {filename}")
                    st.rerun()
                else:
                    st.error("ไม่สามารถโหลดข้อมูลได้")
    
    # --- Question Bank Section ---
    st.markdown("---")
    st.markdown("### 📚 Question Bank")
    
    from .database import get_question_bank_stats, get_question_bank
    
    stats = get_question_bank_stats()
    st.caption(f"💾 {stats['total']} question(s) saved")
    
    if stats['total'] > 0:
        with st.expander("📖 View Saved Questions", expanded=False):
            questions = get_question_bank(limit=10)
            for q in questions:
                st.markdown(f"**{q['bloom_level']}** ({q['difficulty']})")
                st.caption(q['question_text'][:100] + "..." if len(q['question_text']) > 100 else q['question_text'])
                st.markdown("---")

def render_input_studio(start_analysis_callback):
    """ส่วน Input หลัก (Upload + Settings)"""
    
    with st.container(border=True):
        st.markdown(f"#### {t('step1_title')}")
        
        uploaded_file = st.file_uploader(
            t('file_uploader_label'), 
            type=['pdf', 'txt', 'docx'], 
            accept_multiple_files=False, 
            key='file_uploader_widget', 
            label_visibility="visible"
        )

        if uploaded_file:
            st.success(f"✅ Ready: **{uploaded_file.name}** ({round(uploaded_file.size/1024, 1)} KB)")
        else:
            st.info(f"💡 {t('tips_title')}: {t('tip_1')} / {t('tip_2')}")

        st.markdown("###")

        # --- Custom Prompt (Visible) ---
        st.markdown(f"#### ⚙️ {t('advanced_settings')}")
        
        custom_prompt_input = st.text_area(
            "System Instruction",
            value=st.session_state.custom_prompt,
            height=100,
            placeholder=t('custom_prompt_placeholder'), 
            help="ถ้าคุณต้องการกำหนด Prompt เอง ให้พิมพ์ลงในช่องนี้ / ถ้าปล่อยว่าง ระบบจะใช้ Prompt มาตรฐานจากไฟล์ Prompt.txt",
            key='custom_prompt_main',
            label_visibility="collapsed"
        )
        if custom_prompt_input != st.session_state.custom_prompt:
            st.session_state.custom_prompt = custom_prompt_input
            
        st.markdown("###")



        # Logic Update Trigger (Instant Extraction)
        if uploaded_file:
             if uploaded_file.name != st.session_state.last_uploaded_file_name:
                st.session_state.analysis_results = None
                st.session_state.last_uploaded_file_name = uploaded_file.name
                st.session_state.question_texts = None
                
                # --- PERFORM INSTANT EXTRACTION ---
                try:
                    from .utils import extract_text_from_pdf, extract_text_from_docx
                    from .analysis import extract_questions
                    
                    with st.spinner(f"⚡ {t('reading_file')}"):
                        text = ""
                        if uploaded_file.type == "application/pdf":
                            text = extract_text_from_pdf(uploaded_file)
                        elif uploaded_file.type == "text/plain":
                            text = str(uploaded_file.read(), "utf-8")
                            uploaded_file.seek(0)
                        elif "wordprocessingml" in uploaded_file.type: # DOCX
                            text = extract_text_from_docx(uploaded_file)
                        
                        if text:
                            qs = extract_questions(text)
                            if qs:
                                st.session_state.question_texts = qs
                                st.toast(f"✅ พบ {len(qs)} ข้อ! พร้อมวิเคราะห์", icon="⚡")
                                
                                # --- Usability: Preview Extraction ---
                                with st.expander(f"👁️ ตรวจสอบโจทย์ ({len(qs)} ข้อ)", expanded=False):
                                    for i, q in enumerate(qs[:3]):
                                        st.text_area(f"ข้อที่ {i+1}", q.strip(), height=60, disabled=True)
                                    if len(qs) > 3:
                                        st.caption(f"...และอีก {len(qs)-3} ข้อ")
                except Exception as e:
                    st.error(f"Auto-extract failed: {e}")
        
        if st.session_state.question_texts and uploaded_file:
            btn_label = t('analyze_this_file').replace('{filename}', str(uploaded_file.name))
            st.button(
                btn_label, 
                type="primary", 
                use_container_width=True,
                on_click=start_analysis_callback
            )
        elif uploaded_file:
             st.caption(f"⏳ {t('reading_file')}")
        else:
             st.button(t('start_analysis_btn'), disabled=True, use_container_width=True)

    return uploaded_file

def render_dashboard_overview(summary_data, bloom_check):
    """แสดง Dashboard สถิติหลัก"""
    st.markdown(f"### {t('dashboard_overview')}")
    col1, col2, col3, col4 = st.columns(4) 
    
    stats = summary_data["สถิติโดยรวม"]
    def get_val(text): return text.split(' ')[0]
    
    with col1:
        st.metric(t('metric_total'), get_val(stats["จำนวนข้อสอบทั้งหมด"]))
    with col2:
        good_val = get_val(stats["ข้อสอบ **ดี** (ใช้ได้เลย)"])
        st.metric(f"✅ {t('metric_good')}", good_val, delta=t('ready_to_use'))
    with col3:
        bad_val = get_val(stats["ข้อสอบ **ต้องปรับปรุง**"])
        st.metric(f"⚠️ {t('metric_bad')}", bad_val, delta=t('to_improve'), delta_color="inverse")
    with col4:
        if bloom_check['pass']:
             st.metric("Bloom Criteria", "PASS", delta=t('balanced'), delta_color="normal")
        else:
             st.metric("Bloom Criteria", "FAIL", delta=t('unbalanced'), delta_color="inverse")
    st.markdown("---")

def render_detailed_results(all_analysis, bloom_check, summary_data, df):
    """แสดงผลลัพธ์ละเอียด (Charts + Table)"""
    col_chart, col_table = st.columns([1, 1.5])
    
    with col_chart:
        st.markdown(f"##### {t('chart_bloom_dist')}")
        bloom_counts = bloom_check['raw_counts']
        chart_data_raw = {
            'Level': list(bloom_counts.keys())[:-1], 
            'Count': list(bloom_counts.values())[:-1],
            'Color': [get_bloom_color(level) for level in list(bloom_counts.keys())[:-1]]
        }
        chart_df = pd.DataFrame(chart_data_raw)
        
        if not chart_df.empty and chart_df['Count'].sum() > 0:
            base = alt.Chart(chart_df).encode(theta=alt.Theta("Count", stack=True))
            pie = base.mark_arc(outerRadius=100).encode(
                color=alt.Color("Level", scale=alt.Scale(domain=chart_df['Level'].tolist(), range=chart_df['Color'].tolist()), legend=None),
                tooltip=["Level", "Count"],
                order=alt.Order("Count", sort="descending")
            )
            st.altair_chart(pie, use_container_width=True)
        else:
            st.info("No data for chart.")
            
        # --- NEW: Difficulty Curve ---
        st.markdown("##### 📈 Level of Difficulty Trend")
        
        # Prepare Data
        diff_map = {"ง่าย": 1, "ปานกลาง": 2, "ยาก": 3, "Easy": 1, "Medium": 2, "Hard": 3}
        diff_data = []
        for i, item in enumerate(all_analysis, 1):
             d_str = item.get('difficulty', 'ปานกลาง')
             # Clean string to match key
             d_val = 2
             for k, v in diff_map.items():
                 if k in d_str:
                     d_val = v
                     break
             diff_data.append({"Question": i, "Difficulty": d_val, "Label": d_str})
             
        diff_df = pd.DataFrame(diff_data)
        
        if not diff_df.empty:
            line = alt.Chart(diff_df).mark_line(point=True).encode(
                x=alt.X("Question", title="Question Number"),
                y=alt.Y("Difficulty", scale=alt.Scale(domain=[0, 4]), title="Difficulty Level (1-3)"),
                tooltip=["Question", "Label"]
            ).properties(height=200)
            
            st.altair_chart(line, use_container_width=True)
            st.caption("Trend showing difficulty progression across the exam.")

    with col_table:
        st.markdown(f"##### {t('table_quick_summary')}")
        st.dataframe(
            df[['ข้อที่', 'คุณภาพข้อสอบ', 'ระดับความคิด', 'ข้อเสนอแนะ']],
            column_config={
                "คุณภาพข้อสอบ": st.column_config.TextColumn(t('quality'), width="small"),
                "ระดับความคิด": st.column_config.TextColumn("Bloom", width="small"),
            },
            use_container_width=True,
            hide_index=True
        )
        
    st.markdown("---")
    st.markdown(f"#### {t('deep_dive_title')}")
    
    for i, item in enumerate(all_analysis):
        # ... (Existing Expanders)
        # Check for Battle Info
        battle_info = item.get('battle_info')
        
        with st.expander(f"Q{i+1}: {item.get('bloom_level', 'N/A')} - {item.get('difficulty', 'N/A')}", expanded=False):
            # Battle Mode UI
            if battle_info:
                st.info("⚔️ **Battle Mode Result** (Head-to-Head Comparison)")
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    st.markdown(f"**🤖 {battle_info['model_a']}**")
                    st.json(battle_info['result_a'])
                with b_col2:
                    st.markdown(f"**🤖 {battle_info['model_b']}**")
                    st.json(battle_info['result_b'])
                st.markdown("---")
            
            # Standard Details (Merged or Single)
            st.markdown(f"**{t('full_question')}**")
            st.info(st.session_state.question_texts[i] if st.session_state.question_texts and i < len(st.session_state.question_texts) else "N/A")
            
            # Grid Layout for details
            d_c1, d_c2 = st.columns(2)
            with d_c1:
                st.markdown(f"{t('correct_answer')} **{item.get('correct_option', '-')}**")
                st.markdown(f"{t('difficulty')} **{item.get('difficulty', '-')}**")
                st.markdown(f"{t('bloom_level')}: **{item.get('bloom_level', '-')}**")
            with d_c2:
                st.markdown(f"{t('curriculum_indicator')}\n{item.get('curriculum_standard', '-')}")
            
            st.markdown(f"{t('bloom_reason')}\n_{item.get('reasoning', '-')}_")
            
            st.markdown("---")
            st.write(t('answer_analysis_title'))
            st.markdown(f"{t('correct_analysis')}\n{item.get('correct_option_analysis', '-')}")
            st.markdown(f"{t('distractor_analysis')}\n{item.get('distractor_analysis', '-')}")
            st.markdown(f"{t('why_good_distractor')}\n{item.get('why_good_distractor', '-')}")
            
            if item.get('is_good_question'):
                 st.success(f"{t('good')} {t('improvement_suggestion')}\n{item.get('improvement_suggestion')}")
            else:
                 st.error(f"{t('improve')} {t('improvement_suggestion')}\n{item.get('improvement_suggestion')}")
