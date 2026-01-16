# -*- coding: utf-8 -*-
import streamlit as st

# --- Translation Dictionary ---
TRANSLATIONS = {
    'th': {
        # Header
        'app_title': '&#128640; เครื่องมือวิเคราะห์คุณภาพข้อสอบ',
        'app_subtitle': '&#10024; วิเคราะห์ข้อสอบอัตโนมัติด้วย <strong style="color: #667eea;">Gemini AI</strong> ตามหลักสูตรแกนกลางฯ และ <strong style="color: #764ba2;">Bloom\'s Taxonomy</strong>',
        
        # Sidebar
        'sidebar_title': '⚙️ การตั้งค่า & สถานะ AI',
        'ai_connected': '&#9989; เชื่อมต่อ AI สำเร็จ',
        'ai_not_connected': '&#10060; ไม่พบ API Key (GEMINI_API_KEY) - กรุณาตั้งค่าใน `.env`',
        'model_used': '**โมเดลที่ใช้งาน**',
        'batch_analysis': 'Batch Analysis',
        'tips_title': '&#128161; เคล็ดลับ',
        'tip_1': '- ใช้ไฟล์ **PDF** หรือ **TXT**',
        'tip_2': '- ข้อสอบควรมี **เลขข้อ** (เช่น 1., 2.) และ **ตัวเลือก** (เช่น ก., ข.)',
        'api_warning': 'โปรดทราบ: คุณต้องตั้งค่า GEMINI_API_KEY ในไฟล์ .env เพื่อใช้งานส่วนวิเคราะห์',
        
        # Custom Prompt
        'custom_prompt_title': '📝 Custom Prompt (ไม่บังคับ)',
        'custom_prompt_label': 'กรอก Prompt ที่ต้องการใช้แทน Prompt.txt:',
        'custom_prompt_placeholder': 'ปล่อยว่างเพื่อใช้ Prompt จากไฟล์ Prompt.txt...\n\nหรือกรอก Prompt ใหม่ที่นี่ เช่น:\n\nวิเคราะห์ข้อสอบนี้ตามหลัก Bloom\'s Taxonomy และให้คะแนนคุณภาพ...',
        'custom_prompt_active': '&#10024; กำลังใช้ Custom Prompt',
        'custom_prompt_default': '&#128196; กำลังใช้ Prompt จากไฟล์',
        
        # Step 1
        'step1_title': '1️⃣ อัปโหลดไฟล์ข้อสอบ (Batch Analysis)',
        'file_uploader_label': '📁 เลือกไฟล์ข้อสอบ **(.PDF, .DOCX หรือ .TXT)**',
        'reading_file': '⏳ **กำลังอ่านและสกัดข้อสอบ:**',
        'from_file': 'จากไฟล์',
        'extracting': 'กำลังสกัดข้อความ...',
        'no_questions_found': '&#10060; **ไม่พบข้อสอบ** กรุณาตรวจสอบรูปแบบไฟล์ (ไม่มีเลขข้อ/ตัวเลือก หรือรูปแบบซับซ้อนเกินไป)',
        'file_tip': '&#128161; **เคล็ดลับการเตรียมไฟล์:** ไฟล์ควรมี **เลขข้อ** ที่ชัดเจน (เช่น 1., 2., 3.) และมี **ตัวเลือก** (เช่น ก., ข., ค., ง.)',
        'file_read_error': '&#10060; **เกิดข้อผิดพลาดในการอ่านไฟล์:**',
        'extracted_questions': '&#9989; สกัดข้อสอบได้แล้ว **{count} ข้อ** จากไฟล์ `{filename}`',
        
        # Step 2
        'step2_title': '2️⃣ เริ่มต้นวิเคราะห์และสร้างรายงาน &#128640;',
        'start_analysis_btn': '&#128640; **กดที่นี่เพื่อเริ่มการวิเคราะห์ด้วย AI**',
        'api_not_ready': 'Key ไม่พร้อมใช้งาน กรุณาตรวจสอบการตั้งค่า',
        'starting_analysis': '&#128640; **กำลังเริ่มการวิเคราะห์ด้วย AI...**',
        'preparing_analysis': '⏳ กำลังเตรียมวิเคราะห์ข้อสอบ {count} ข้อ โดยใช้ `{model}`',
        'analyzing_question': '&#129302; วิเคราะห์ข้อที่ {num}...',
        'analysis_progress': 'กำลังวิเคราะห์ข้อสอบ {current}/{total} ข้อ...',
        'analysis_complete': '🎉 **การวิเคราะห์เสร็จสมบูรณ์!**',
        
        # Step 3 - Results
        'step3_title': '3️⃣ ผลการวิเคราะห์ชุดข้อสอบ 📝',
        'tab_summary': '📊 สรุปรายงาน & เกณฑ์ Bloom',
        'tab_details': '📝 รายละเอียดรายข้อ',
        'summary_title': '📊 สรุปภาพรวมคุณภาพข้อสอบ',
        'good_questions': '&#9989; ข้อสอบคุณภาพดี',
        'needs_improvement': '&#9888; ข้อสอบต้องปรับปรุง',
        'total_questions': '📝 จำนวนข้อสอบทั้งหมด',
        'analyzed_success': '&#129302; วิเคราะห์สำเร็จ',
        'bloom_criteria_title': '&#128161; เกณฑ์การกระจายระดับความคิด (Bloom)',
        'bloom_low': 'ระดับความคิดต่ำ (จำ/เข้าใจ)',
        'bloom_mid': 'ระดับความคิดกลาง (ใช้/วิเคราะห์)',
        'bloom_high': 'ระดับความคิดสูง (ประเมิน/สร้างสรรค์)',
        'target': 'เป้าหมาย',
        'unidentified_bloom': '**ข้อที่ระบุระดับความคิดไม่ได้:**',
        'bloom_distribution': '📈 การกระจายระดับ Bloom\'s Taxonomy',
        'bloom_table_title': '**ตารางสรุปจำนวนและคุณภาพข้อสอบตามระดับ Bloom**',
        'details_title': '📝 รายละเอียดผลการวิเคราะห์รายข้อ',
        'click_detail': '### 🔎 คลิกดูรายละเอียดการวิเคราะห์ (10 Fields) รายข้อ',
        'question_num': 'ข้อที่',
        'quality': 'คุณภาพข้อสอบ',
        'bloom_level': 'ระดับความคิด',
        'curriculum': 'มาตรฐานหลักสูตร',
        'answer': 'คำตอบ',
        'reasoning': 'เหตุผลโดยย่อ',
        'suggestion': 'ข้อเสนอแนะ',
        'full_question': '**คำถามเต็ม:**',
        'good': '&#9989; คุณภาพดี',
        'improve': '&#10060; ต้องปรับปรุง/ล้มเหลว',
        'difficulty': '⚖️ ความยาก:',
        'correct_answer': '&#9989; คำตอบ:',
        'curriculum_indicator': '**&#128218; ตัวชี้วัดหลักสูตร:**',
        'bloom_reason': '**&#129504; เหตุผลของระดับ Bloom/คุณภาพ:**',
        'answer_analysis_title': 'วิเคราะห์คำตอบและตัวลวง',
        'correct_analysis': '**&#9989; วิเคราะห์คำตอบที่ถูก:**',
        'distractor_analysis': '**&#10060; วิเคราะห์ตัวเลือกลวง (Distractors):**',
        'why_good_distractor': '**&#128161; เหตุผลที่ตัวลวงดี:**',
        'improvement_suggestion': '**🔧 ข้อเสนอแนะในการปรับปรุง:**',
        
        # Quota Warning
        'quota_warning': '&#9888; **ข้อจำกัด Free Tier:** 20 requests/วัน หากเกินโควต้า กรุณารอ 24 ชั่วโมง หรืออัปเกรดแผนการใช้งาน',
        
        # Language
        'language_btn': '🌐 English',

        # --- New Dashboard Keys ---
        'dashboard_overview': '📊 ภาพรวมการวิเคราะห์',
        'metric_total': 'จำนวนข้อทั้งหมด',
        'metric_good': 'ข้อสอบคุณภาพดี',
        'ready_to_use': 'ใช้ได้เลย',
        'metric_bad': 'ต้องปรับปรุง',
        'to_improve': 'ต้องแก้ไข',
        'metric_bloom_pass': 'เกณฑ์ Bloom: ผ่าน',
        'metric_bloom_fail': 'เกณฑ์ Bloom: ไม่ผ่าน',
        'balanced': 'สมดุลดี',
        'unbalanced': 'ไม่สมดุล',
        'chart_bloom_dist': '📈 การกระจายตัว Bloom\'s Taxonomy',
        'table_quick_summary': '📋 สรุปย่อ',
        'deep_dive_title': '📝 เจาะลึกรายข้อ',
        'auto_fix_btn': '✨ แก้ไขอัตโนมัติ',
        'gen_exam_title': '✨ สร้างข้อสอบด้วย AI',
        'ai_config': '⚙️ ตั้งค่า AI',
        'provider_label': 'ผู้ให้บริการ',
        'model_label': 'โมเดล',
        'advanced_settings': '⚙️ ตั้งค่าเพิ่มเติม (Custom Prompt)',
        'analyze_this_file': '🚀 วิเคราะห์ไฟล์: {filename}',
        'curriculum_upload_title': '📚 อัปโหลดหลักสูตร (PDF)',
    },
    'en': {
        # ... (Existing English keys)
        'curriculum_upload_title': '📚 Upload Curriculum (PDF)',
        'app_title': '&#128640; Exam Quality Analysis Tool',
        'app_subtitle': '&#10024; Automatic exam analysis with <strong style="color: #667eea;">Gemini AI</strong> based on Core Curriculum and <strong style="color: #764ba2;">Bloom\'s Taxonomy</strong>',
        
        # Sidebar
        'sidebar_title': '⚙️ Settings & AI Status',
        'ai_connected': '&#9989; AI Connected Successfully',
        'ai_not_connected': '&#10060; API Key not found (GEMINI_API_KEY) - Please set in `.env`',
        'model_used': '**Model Used**',
        'batch_analysis': 'Batch Analysis',
        'tips_title': '&#128161; Tips',
        'tip_1': '- Use **PDF** or **TXT** files',
        'tip_2': '- Questions should have **numbers** (e.g., 1., 2.) and **choices** (e.g., A., B.)',
        'api_warning': 'Note: You must set GEMINI_API_KEY in .env file to use the analysis feature',
        
        # Custom Prompt
        'custom_prompt_title': '📝 Custom Prompt (Optional)',
        'custom_prompt_label': 'Enter custom prompt to use instead of Prompt.txt:',
        'custom_prompt_placeholder': 'Leave empty to use default Prompt.txt...\n\nOr enter your custom prompt here, e.g.:\n\nAnalyze this exam question according to Bloom\'s Taxonomy and rate its quality...',
        'custom_prompt_active': '&#10024; Using Custom Prompt',
        'custom_prompt_default': '&#128196; Using Default Prompt File',
        
        # Step 1
        'step1_title': '1️⃣ Upload Exam File (Batch Analysis)',
        'file_uploader_label': '📁 Select exam file **(.PDF, .DOCX or .TXT)**',
        'reading_file': '⏳ **Reading and extracting questions:**',
        'from_file': 'from file',
        'extracting': 'Extracting text...',
        'no_questions_found': '&#10060; **No questions found** Please check the file format (no question numbers/choices or format too complex)',
        'file_tip': '&#128161; **File preparation tip:** File should have clear **question numbers** (e.g., 1., 2., 3.) and **choices** (e.g., A., B., C., D.)',
        'file_read_error': '&#10060; **Error reading file:**',
        'extracted_questions': '&#9989; Extracted **{count} questions** from file `{filename}`',
        
        # Step 2
        'step2_title': '2️⃣ Start Analysis & Generate Report &#128640;',
        'start_analysis_btn': '&#128640; **Click here to start AI analysis**',
        'api_not_ready': 'API Key not ready. Please check settings',
        'starting_analysis': '&#128640; **Starting AI analysis...**',
        'preparing_analysis': '⏳ Preparing to analyze {count} questions using `{model}`',
        'analyzing_question': '&#129302; Analyzing question {num}...',
        'analysis_progress': 'Analyzing question {current}/{total}...',
        'analysis_complete': '🎉 **Analysis Complete!**',
        
        # Step 3 - Results
        'step3_title': '3️⃣ Exam Analysis Results 📝',
        'tab_summary': '📊 Summary & Bloom Criteria',
        'tab_details': '📝 Question Details',
        'summary_title': '📊 Overall Exam Quality Summary',
        'good_questions': '&#9989; Good Quality Questions',
        'needs_improvement': '&#9888; Needs Improvement',
        'total_questions': '📝 Total Questions',
        'analyzed_success': '&#129302; Successfully Analyzed',
        'bloom_criteria_title': '&#128161; Bloom\'s Taxonomy Distribution Criteria',
        'bloom_low': 'Lower Order (Remember/Understand)',
        'bloom_mid': 'Middle Order (Apply/Analyze)',
        'bloom_high': 'Higher Order (Evaluate/Create)',
        'target': 'Target',
        'unidentified_bloom': '**Questions with unidentified Bloom level:**',
        'bloom_distribution': '📈 Bloom\'s Taxonomy Distribution',
        'bloom_table_title': '**Summary Table: Questions by Bloom Level**',
        'details_title': '📝 Detailed Analysis per Question',
        'click_detail': '### 🔎 Click to view detailed analysis (10 Fields) per question',
        'question_num': 'Q#',
        'quality': 'Quality',
        'bloom_level': 'Bloom Level',
        'curriculum': 'Curriculum Standard',
        'answer': 'Answer',
        'reasoning': 'Brief Reasoning',
        'suggestion': 'Suggestion',
        'full_question': '**Full Question:**',
        'good': '&#9989; Good',
        'improve': '&#10060; Needs Improvement/Failed',
        'difficulty': '⚖️ Difficulty:',
        'correct_answer': '&#9989; Answer:',
        'curriculum_indicator': '**&#128218; Curriculum Indicator:**',
        'bloom_reason': '**&#129504; Bloom Level/Quality Reasoning:**',
        'answer_analysis_title': 'Answer & Distractor Analysis',
        'correct_analysis': '**&#9989; Correct Answer Analysis:**',
        'distractor_analysis': '**&#10060; Distractor Analysis:**',
        'why_good_distractor': '**&#128161; Why Good Distractors:**',
        'improvement_suggestion': '**🔧 Improvement Suggestion:**',
        
        # Quota Warning
        'quota_warning': '&#9888; **Free Tier Limit:** 20 requests/day. If exceeded, please wait 24 hours or upgrade your plan.',
        
        # Language
        'language_btn': '🌐 ภาษาไทย',

        # --- New Dashboard Keys ---
        'dashboard_overview': '📊 Analysis Overview',
        'metric_total': 'Total Questions',
        'metric_good': 'Good Quality',
        'ready_to_use': 'Ready to use',
        'metric_bad': 'Needs Work',
        'to_improve': 'To Improve',
        'metric_bloom_pass': 'Bloom Criteria: PASS',
        'metric_bloom_fail': 'Bloom Criteria: FAIL',
        'balanced': 'Balanced',
        'unbalanced': 'Unbalanced',
        'chart_bloom_dist': '📈 Bloom\'s Taxonomy Dist.',
        'table_quick_summary': '📋 Quick Summary',
        'deep_dive_title': '📝 Question Deep Dive',
        'auto_fix_btn': '✨ Auto-Fix Question',
        'gen_exam_title': '✨ AI Exam Generator',
        'ai_config': '⚙️ AI Config',
        'provider_label': 'Provider',
        'model_label': 'Model',
        'advanced_settings': '⚙️ Advanced Settings (Custom Prompt)',
        'analyze_this_file': '🚀 Analyze: {filename}',
    }
}

def t(key, default=None):
    """Get translation for current language"""
    lang = st.session_state.get('language', 'th')
    val = TRANSLATIONS.get(lang, TRANSLATIONS['th']).get(key)
    if val:
        return val
    return default if default else key

def toggle_language():
    if st.session_state.language == 'th':
        st.session_state.language = 'en'
    else:
        st.session_state.language = 'th'
    
    # 🔄 Reset Analysis Results to force AI re-generation in new language
    st.session_state.analysis_results = None
