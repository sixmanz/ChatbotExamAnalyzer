import os
import sys
import subprocess
import json
import re
import io
import time
import pandas as pd
from dotenv import load_dotenv
import streamlit as st
from PyPDF2 import PdfReader 
import google.generativeai as genai
from google.generativeai import types
from google.generativeai.types import GenerationConfig 
from typing import Dict, Any, Tuple
import altair as alt 


# --- 1. การตั้งค่าและโหลด Environment ---
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()

# โมเดลที่ใช้ 
GEMINI_BATCH_MODEL_NAME = "gemini-2.5-flash" 

GEMINI_AVAILABLE = False
try:
    if GEMINI_API_KEY and len(GEMINI_API_KEY) > 30:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


# Initialize session states
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'last_uploaded_file_name' not in st.session_state:
    st.session_state.last_uploaded_file_name = None
if 'question_texts' not in st.session_state:
    st.session_state.question_texts = None
if 'language' not in st.session_state:
    st.session_state.language = 'th'  # Default to Thai
if 'custom_prompt' not in st.session_state:
    st.session_state.custom_prompt = ""  # Custom prompt (empty = use default)

# --- Translation Dictionary ---
TRANSLATIONS = {
    'th': {
        # Header
        'app_title': '🚀 เครื่องมือวิเคราะห์คุณภาพข้อสอบ',
        'app_subtitle': '✨ วิเคราะห์ข้อสอบอัตโนมัติด้วย <strong style="color: #667eea;">Gemini AI</strong> ตามหลักสูตรแกนกลางฯ และ <strong style="color: #764ba2;">Bloom\'s Taxonomy</strong>',
        
        # Sidebar
        'sidebar_title': '⚙️ การตั้งค่า & สถานะ AI',
        'ai_connected': '✅ เชื่อมต่อ AI สำเร็จ',
        'ai_not_connected': '❌ ไม่พบ API Key (GEMINI_API_KEY) - กรุณาตั้งค่าใน `.env`',
        'model_used': '**โมเดลที่ใช้งาน**',
        'batch_analysis': 'Batch Analysis',
        'tips_title': '💡 เคล็ดลับ',
        'tip_1': '- ใช้ไฟล์ **PDF** หรือ **TXT**',
        'tip_2': '- ข้อสอบควรมี **เลขข้อ** (เช่น 1., 2.) และ **ตัวเลือก** (เช่น ก., ข.)',
        'api_warning': 'โปรดทราบ: คุณต้องตั้งค่า GEMINI_API_KEY ในไฟล์ .env เพื่อใช้งานส่วนวิเคราะห์',
        
        # Custom Prompt
        'custom_prompt_title': '📝 Custom Prompt (ไม่บังคับ)',
        'custom_prompt_label': 'กรอก Prompt ที่ต้องการใช้แทน Prompt.txt:',
        'custom_prompt_placeholder': 'ปล่อยว่างเพื่อใช้ Prompt จากไฟล์ Prompt.txt...\n\nหรือกรอก Prompt ใหม่ที่นี่ เช่น:\n\nวิเคราะห์ข้อสอบนี้ตามหลัก Bloom\'s Taxonomy และให้คะแนนคุณภาพ...',
        'custom_prompt_active': '✨ กำลังใช้ Custom Prompt',
        'custom_prompt_default': '📄 กำลังใช้ Prompt จากไฟล์',
        
        # Step 1
        'step1_title': '1️⃣ อัปโหลดไฟล์ข้อสอบ (Batch Analysis)',
        'file_uploader_label': '📁 เลือกไฟล์ข้อสอบ **(.PDF หรือ .TXT)**',
        'reading_file': '⏳ **กำลังอ่านและสกัดข้อสอบ:**',
        'from_file': 'จากไฟล์',
        'extracting': 'กำลังสกัดข้อความ...',
        'no_questions_found': '❌ **ไม่พบข้อสอบ** กรุณาตรวจสอบรูปแบบไฟล์ (ไม่มีเลขข้อ/ตัวเลือก หรือรูปแบบซับซ้อนเกินไป)',
        'file_tip': '💡 **เคล็ดลับการเตรียมไฟล์:** ไฟล์ควรมี **เลขข้อ** ที่ชัดเจน (เช่น 1., 2., 3.) และมี **ตัวเลือก** (เช่น ก., ข., ค., ง.)',
        'file_read_error': '❌ **เกิดข้อผิดพลาดในการอ่านไฟล์:**',
        'extracted_questions': '✅ สกัดข้อสอบได้แล้ว **{count} ข้อ** จากไฟล์ `{filename}`',
        
        # Step 2
        'step2_title': '2️⃣ เริ่มต้นวิเคราะห์และสร้างรายงาน 🚀',
        'start_analysis_btn': '🚀 **กดที่นี่เพื่อเริ่มการวิเคราะห์ด้วย AI**',
        'api_not_ready': 'Key ไม่พร้อมใช้งาน กรุณาตรวจสอบการตั้งค่า',
        'starting_analysis': '🚀 **กำลังเริ่มการวิเคราะห์ด้วย AI...**',
        'preparing_analysis': '⏳ กำลังเตรียมวิเคราะห์ข้อสอบ {count} ข้อ โดยใช้ `{model}`',
        'analyzing_question': '🤖 วิเคราะห์ข้อที่ {num}...',
        'analysis_progress': 'กำลังวิเคราะห์ข้อสอบ {current}/{total} ข้อ...',
        'analysis_complete': '🎉 **การวิเคราะห์เสร็จสมบูรณ์!**',
        
        # Step 3 - Results
        'step3_title': '3️⃣ ผลการวิเคราะห์ชุดข้อสอบ 📝',
        'tab_summary': '📊 สรุปรายงาน & เกณฑ์ Bloom',
        'tab_details': '📝 รายละเอียดรายข้อ',
        'summary_title': '📊 สรุปภาพรวมคุณภาพข้อสอบ',
        'good_questions': '✅ ข้อสอบคุณภาพดี',
        'needs_improvement': '⚠️ ข้อสอบต้องปรับปรุง',
        'total_questions': '📝 จำนวนข้อสอบทั้งหมด',
        'analyzed_success': '🤖 วิเคราะห์สำเร็จ',
        'bloom_criteria_title': '💡 เกณฑ์การกระจายระดับความคิด (Bloom)',
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
        'good': '✅ คุณภาพดี',
        'improve': '❌ ต้องปรับปรุง/ล้มเหลว',
        'difficulty': '⚖️ ความยาก:',
        'correct_answer': '✅ คำตอบ:',
        'curriculum_indicator': '**📚 ตัวชี้วัดหลักสูตร:**',
        'bloom_reason': '**🧠 เหตุผลของระดับ Bloom/คุณภาพ:**',
        'answer_analysis_title': 'วิเคราะห์คำตอบและตัวลวง',
        'correct_analysis': '**✅ วิเคราะห์คำตอบที่ถูก:**',
        'distractor_analysis': '**❌ วิเคราะห์ตัวเลือกลวง (Distractors):**',
        'why_good_distractor': '**💡 เหตุผลที่ตัวลวงดี:**',
        'improvement_suggestion': '**🔧 ข้อเสนอแนะในการปรับปรุง:**',
        
        # Quota Warning
        'quota_warning': '⚠️ **ข้อจำกัด Free Tier:** 20 requests/วัน หากเกินโควต้า กรุณารอ 24 ชั่วโมง หรืออัปเกรดแผนการใช้งาน',
        
        # Language
        'language_btn': '🌐 English',
    },
    'en': {
        # Header
        'app_title': '🚀 Exam Quality Analysis Tool',
        'app_subtitle': '✨ Automatic exam analysis with <strong style="color: #667eea;">Gemini AI</strong> based on Core Curriculum and <strong style="color: #764ba2;">Bloom\'s Taxonomy</strong>',
        
        # Sidebar
        'sidebar_title': '⚙️ Settings & AI Status',
        'ai_connected': '✅ AI Connected Successfully',
        'ai_not_connected': '❌ API Key not found (GEMINI_API_KEY) - Please set in `.env`',
        'model_used': '**Model Used**',
        'batch_analysis': 'Batch Analysis',
        'tips_title': '💡 Tips',
        'tip_1': '- Use **PDF** or **TXT** files',
        'tip_2': '- Questions should have **numbers** (e.g., 1., 2.) and **choices** (e.g., A., B.)',
        'api_warning': 'Note: You must set GEMINI_API_KEY in .env file to use the analysis feature',
        
        # Custom Prompt
        'custom_prompt_title': '📝 Custom Prompt (Optional)',
        'custom_prompt_label': 'Enter custom prompt to use instead of Prompt.txt:',
        'custom_prompt_placeholder': 'Leave empty to use default Prompt.txt...\n\nOr enter your custom prompt here, e.g.:\n\nAnalyze this exam question according to Bloom\'s Taxonomy and rate its quality...',
        'custom_prompt_active': '✨ Using Custom Prompt',
        'custom_prompt_default': '📄 Using Default Prompt File',
        
        # Step 1
        'step1_title': '1️⃣ Upload Exam File (Batch Analysis)',
        'file_uploader_label': '📁 Select exam file **(.PDF or .TXT)**',
        'reading_file': '⏳ **Reading and extracting questions:**',
        'from_file': 'from file',
        'extracting': 'Extracting text...',
        'no_questions_found': '❌ **No questions found** Please check the file format (no question numbers/choices or format too complex)',
        'file_tip': '💡 **File preparation tip:** File should have clear **question numbers** (e.g., 1., 2., 3.) and **choices** (e.g., A., B., C., D.)',
        'file_read_error': '❌ **Error reading file:**',
        'extracted_questions': '✅ Extracted **{count} questions** from file `{filename}`',
        
        # Step 2
        'step2_title': '2️⃣ Start Analysis & Generate Report 🚀',
        'start_analysis_btn': '🚀 **Click here to start AI analysis**',
        'api_not_ready': 'API Key not ready. Please check settings',
        'starting_analysis': '🚀 **Starting AI analysis...**',
        'preparing_analysis': '⏳ Preparing to analyze {count} questions using `{model}`',
        'analyzing_question': '🤖 Analyzing question {num}...',
        'analysis_progress': 'Analyzing question {current}/{total}...',
        'analysis_complete': '🎉 **Analysis Complete!**',
        
        # Step 3 - Results
        'step3_title': '3️⃣ Exam Analysis Results 📝',
        'tab_summary': '📊 Summary & Bloom Criteria',
        'tab_details': '📝 Question Details',
        'summary_title': '📊 Overall Exam Quality Summary',
        'good_questions': '✅ Good Quality Questions',
        'needs_improvement': '⚠️ Needs Improvement',
        'total_questions': '📝 Total Questions',
        'analyzed_success': '🤖 Successfully Analyzed',
        'bloom_criteria_title': '💡 Bloom\'s Taxonomy Distribution Criteria',
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
        'good': '✅ Good',
        'improve': '❌ Needs Improvement/Failed',
        'difficulty': '⚖️ Difficulty:',
        'correct_answer': '✅ Answer:',
        'curriculum_indicator': '**📚 Curriculum Indicator:**',
        'bloom_reason': '**🧠 Bloom Level/Quality Reasoning:**',
        'answer_analysis_title': 'Answer & Distractor Analysis',
        'correct_analysis': '**✅ Correct Answer Analysis:**',
        'distractor_analysis': '**❌ Distractor Analysis:**',
        'why_good_distractor': '**💡 Why Good Distractors:**',
        'improvement_suggestion': '**🔧 Improvement Suggestion:**',
        
        # Quota Warning
        'quota_warning': '⚠️ **Free Tier Limit:** 20 requests/day. If exceeded, please wait 24 hours or upgrade your plan.',
        
        # Language
        'language_btn': '🌐 ภาษาไทย',
    }
}

def t(key):
    """Get translation for current language"""
    lang = st.session_state.get('language', 'th')
    return TRANSLATIONS.get(lang, TRANSLATIONS['th']).get(key, key)


# --- 2. การโหลด Prompt Template ---
def load_prompts() -> Tuple[str, str]:
    """อ่านเนื้อหา Prompt Template จากไฟล์ 'Prompt.txt' และแยกเป็น System/Chat"""
    prompt_path = os.path.join(os.path.dirname(__file__), 'Prompt.txt')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            full_content = f.read()
            
            # 1. System Instruction
            system_match = full_content.split("# --- END_SYSTEM_INSTRUCTION_ANALYSIS_MODE ---")[0]
            SYSTEM_INSTRUCTION_PROMPT = system_match.strip() if system_match else "You are a test expert for Thai curriculum. Analyze the question and return a JSON object."
            
            # 2. Few-Shot Template 
            chat_match = full_content.split("# --- CHAT_PROMPT ---")
            
            if len(chat_match) > 1:
                # แยกส่วน Prompt Template ทั้งหมด
                template_content = chat_match[1].split("# --- CHAT_PROMPT_END ---")[0].strip()
                # และเพิ่ม {user_query} เข้าไปในส่วนท้าย
                FEW_SHOT_PROMPT_TEMPLATE = template_content + "\n{user_query}"
            else:
                FEW_SHOT_PROMPT_TEMPLATE = "Analyze the following question/text and return the JSON object: {user_query}"

            return SYSTEM_INSTRUCTION_PROMPT, FEW_SHOT_PROMPT_TEMPLATE
    except FileNotFoundError:
        return (
            "# Error: Prompt file not found. Fallback to default instruction.", 
            "Analyze the following question/text and return the JSON object: {user_query}"
        )

SYSTEM_INSTRUCTION_PROMPT, FEW_SHOT_PROMPT_TEMPLATE = load_prompts()


# --- 3. Helper Functions ---

BLOOM_COLORS = {
    "REMEMBER": "#6495ED",  
    "UNDERSTAND": "#40E0D0",
    "APPLY": "#50C878",     
    "ANALYZE": "#8FBC8F",   
    "EVALUATE": "#ADFF2F",  
    "CREATE": "#FFD700",    
    "ไม่ระบุ": "#A9A9A9",
    "ไม่สามารถระบุได้": "#A9A9A9"
}

def get_bloom_color(level):
    """ส่งคืนรหัสสี Hex ตามระดับ Bloom's Taxonomy"""
    if not level:
        return BLOOM_COLORS['ไม่ระบุ']
    
    level_upper = level.strip().upper()
    for key, color in BLOOM_COLORS.items():
        if key in level_upper:
            return color
    return BLOOM_COLORS['ไม่ระบุ'] # Fallback

def get_text_color_for_bloom(level):
    """กำหนดสีตัวอักษรให้ตัดกับสีพื้นหลัง (เพื่อให้มองเห็นได้ชัดเจน)"""
    level_upper = level.strip().upper()
    if level_upper in ['EVALUATE', 'CREATE']: # สีเหลือง/ทอง/สว่าง ควรใช้ตัวอักษรสีดำ
        return 'black' 
    return 'white' # สีเข้มอื่นๆ ใช้ตัวอักษรสีขาว


def extract_text_from_pdf(pdf_reader):
    """สกัดข้อความจากวัตถุ PdfReader"""
    text = ""
    for page in pdf_reader.pages:
        try:
            page_text = page.get_text() if hasattr(page, 'get_text') else page.extract_text()
            text += (page_text or "") + "\n"
        except Exception:
            text += "\n"
    return text.strip()

def clean_and_normalize(text):
    """ทำความสะอาดข้อความและแปลงเลขไทยเป็นเลขอารบิก"""
    if not text: return ""
    # 1. แปลงเลขไทย
    thai_digits = "๐๑๒๓๔๕๖๗๘๙"
    for i, digit in enumerate(thai_digits):
        text = text.replace(digit, str(i))
    
    # 2. ทำความสะอาดตัวอักษรพิเศษและช่องว่าง
    text = re.sub(r'[ \t]+', ' ', text) 
    text = text.replace('\r', '')
    
    # 3. ทำให้ตัวเลือกติดกับจุด (เช่น ก . -> ก.)
    text = re.sub(r'([ก-งA-D])\s*\.', r'\1.', text)
    
    # 4. ทำให้เลขข้อติดกับจุด (เช่น 1 . -> 1.)
    text = re.sub(r'(\d+)\s*\.', r'\1.', text)
    
    # 5. ลบบรรทัดว่างที่ติดกันหลายบรรทัด
    text = re.sub(r'\n{2,}', '\n', text)
    
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)

def extract_questions(raw_text):
    """
    สกัดข้อสอบเป็นรายข้อ (เน้นความแม่นยำในการจับคู่ 1-99 และตัวเลือก ก. ข.)
    """
    # 1. ทำความสะอาดข้อความทั้งหมด
    # ตัดส่วน "เฉลย" ทิ้ง เพื่อให้ AI วิเคราะห์เอง
    text = re.split(r"={10,}\s*เฉลย\s*={10,}", raw_text, flags=re.DOTALL | re.IGNORECASE)[0]
    cleaned_text = clean_and_normalize(text)
    
    # 2. สร้าง Regex สำหรับจับเลขข้อ (จำกัดแค่ตัวเลข 1-99)
    question_prefix = r'(?:[1-9]\d?\.|\([1-9]\d?\))\s*' 
    
    # 3. สร้าง Regex สำหรับตัวเลือก (Thai/English)
    option_marker = r'(?:ก\.\s*|A\.\s*)'
    
    # 4. รวม Regex: จับกลุ่มที่ขึ้นต้นด้วยเลขข้อ (1-99) และมีตัวเลือก ก./A. ตามมา
    pattern = r'(\s*' + question_prefix + r'.*?' + option_marker + r'.*?)(?=\s*' + question_prefix + r'|\s*$)'
    
    # ค้นหาข้อสอบทั้งหมด
    matches = re.findall(pattern, cleaned_text, flags=re.DOTALL | re.IGNORECASE)
    
    questions = []
    
    # 5. การตรวจสอบความถูกต้องและจัดรูปแบบ
    for m in matches:
        q = m.strip()
        
        # ตรวจสอบว่ามีตัวเลือก ก-ง หรือ A-D อย่างน้อย 2 ตัวหรือไม่
        option_count_thai = len(re.findall(r'[ก-ง]\s*\.', q))
        option_count_eng = len(re.findall(r'[A-D]\s*\.', q))
        
        # เงื่อนไข: ต้องมีตัวเลือกอย่างน้อย 2 ตัว
        if option_count_thai >= 2 or option_count_eng >= 2:
            # พยายามแยกตัวเลือกแต่ละตัวให้ขึ้นบรรทัดใหม่
            q_formatted = re.sub(r'(\s*[กขคง]\s*\.)', r'\n\1', q)
            q_formatted = re.sub(r'(\s*[A-D]\s*\.)', r'\n\1', q_formatted)
            questions.append(q_formatted.strip())
        
    return questions


def analyze_with_gemini(question_text, question_id=1):
    """เรียกใช้ Gemini API เพื่อวิเคราะห์ข้อสอบ (10 Fields Logic)"""
    if not GEMINI_AVAILABLE:
        return {
            "bloom_level": "ไม่ระบุ", "reasoning": "ไม่พบ API Key",
            "difficulty": "ไม่ระบุ", "curriculum_standard": "ไม่ระบุ",
            "correct_option": "ไม่ระบุ", "correct_option_analysis": "ไม่มีการเชื่อมต่อ AI",
            "distractor_analysis": "ไม่มีการเชื่อมต่อ AI", "why_good_distractor": "ไม่มีการเชื่อมต่อ AI",
            "is_good_question": False, "improvement_suggestion": "ไม่สามารถวิเคราะห์ได้: ไม่พบ API Key"
        } 

    # Check for custom prompt
    custom_prompt = st.session_state.get('custom_prompt', '').strip()
    
    if custom_prompt:
        # Use custom prompt as system instruction
        system_instruction = custom_prompt
        prompt_template = "{user_query}"  # Simple template for custom prompt
    else:
        # Use default prompts from Prompt.txt
        system_instruction = SYSTEM_INSTRUCTION_PROMPT
        prompt_template = FEW_SHOT_PROMPT_TEMPLATE

    model = genai.GenerativeModel(
        GEMINI_BATCH_MODEL_NAME, 
        system_instruction=system_instruction
    )
    
    question_text_formatted = f"คำถามข้อที่ {question_id}:\n{question_text}"
    
    # การจัดรูปแบบ Prompt ที่ถูกต้อง
    full_prompt = prompt_template.format(user_query=question_text_formatted) 
    
    # กำหนด JSON Schema (10 Fields)
    json_schema = {
        "type": "object",
        "properties": {
            "bloom_level": {"type": "string"},
            "reasoning": {"type": "string"},
            "difficulty": {"type": "string"},
            "curriculum_standard": {"type": "string"},
            "correct_option": {"type": "string"},
            "correct_option_analysis": {"type": "string"},
            "distractor_analysis": {"type": "string"},
            "why_good_distractor": {"type": "string"},
            "is_good_question": {"type": "boolean"},
            "improvement_suggestion": {"type": "string"}
        },
        "required": [
            "bloom_level", "reasoning", "difficulty", "curriculum_standard",
            "correct_option", "correct_option_analysis", "distractor_analysis",
            "why_good_distractor", "is_good_question", "improvement_suggestion"
        ]
    }

    # กำหนด Config (บังคับ JSON และลด Temperature)
    config = GenerationConfig( 
        response_mime_type="application/json", 
        response_schema=json_schema, 
        temperature=0.0
    )
    
    last_error_message = ""

    for attempt in range(3):
        delay = 2 ** attempt
        if attempt > 0:
            time.sleep(delay)
            
        try:
            response = model.generate_content(
                full_prompt, 
                generation_config=config, 
            )
            raw_text = response.text.strip()
        
            # Hardened JSON Cleaning/Extraction
            cleaned_json = re.sub(r'^```(?:json)?\s*|```$', '', raw_text, flags=re.MULTILINE | re.DOTALL).strip()
            start_brace = cleaned_json.find('{')
            end_brace = cleaned_json.rfind('}')
            
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                cleaned_json = cleaned_json[start_brace:end_brace+1].strip()
            else:
                raise ValueError("Could not find valid JSON structure (missing { or }).") 
            
            # โหลด JSON
            analysis = json.loads(cleaned_json)
            
            # Data sanitation and Key validation
            required_keys = [
                "bloom_level", "reasoning", "difficulty", "curriculum_standard",
                "correct_option", "correct_option_analysis", "distractor_analysis",
                "why_good_distractor", "is_good_question", "improvement_suggestion"
            ]
            
            def safe_str(val): return str(val).strip() if val is not None else "ไม่ระบุ"
            def safe_bool(val):
                if isinstance(val, str): 
                    return val.lower().strip() == 'true'
                if val in (True, False): return val
                return False

            final_analysis = {}
            for key in required_keys:
                raw_val = analysis.get(key)
                if key == "is_good_question":
                    final_analysis[key] = safe_bool(raw_val)
                else:
                    final_analysis[key] = safe_str(raw_val if raw_val is not None else "ไม่ระบุ")
                
                if key not in analysis:
                    raise KeyError(f"JSON Output is missing required key: {key}")

            return final_analysis

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_error_message = f"ข้อผิดพลาดในการประมวลผล JSON/Key: {type(e).__name__}: {str(e)}"
            continue # ลองใหม่ (Retry)
            
        except Exception as e:
            error_str = str(e)
            # Handle Rate Limit / Quota Exceeded (429 Error)
            if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
                # Extract retry delay if available
                retry_delay = 30  # Default 30 seconds
                import re as regex_module
                delay_match = regex_module.search(r'retry.*?(\d+)', error_str.lower())
                if delay_match:
                    retry_delay = int(delay_match.group(1)) + 5  # Add 5 seconds buffer
                
                last_error_message = f"⏳ Rate Limit: รอ {retry_delay} วินาที แล้วลองใหม่..."
                
                # Auto-retry after waiting
                if attempt < 2:  # Only wait and retry if not last attempt
                    time.sleep(retry_delay)
                    continue
                else:
                    last_error_message = f"❌ Quota Exceeded: คุณใช้โควต้า API ครบแล้ว กรุณารอ 24 ชั่วโมง หรืออัปเกรดแผนการใช้งาน"
                    break
            else:
                last_error_message = f"ข้อผิดพลาด: {type(e).__name__}: {str(e)}"
                continue

    # Fallback สุดท้าย: หาก AI วิเคราะห์ไม่ได้เลย
    return {
        "bloom_level": "ไม่สามารถระบุได้", "reasoning": "AI วิเคราะห์ล้มเหลว",
        "difficulty": "ไม่สามารถประเมินได้", "curriculum_standard": "ไม่สามารถระบุได้",
        "correct_option": "ไม่ระบุ", "correct_option_analysis": "ไม่ระบุ",
        "distractor_analysis": "ไม่ระบุ", "why_good_distractor": "ไม่ระบุ",
        "is_good_question": False, 
        "improvement_suggestion": f"**เกิดข้อผิดพลาดในการวิเคราะห์**: {last_error_message}"
    }


def check_bloom_criteria(analysis_results):
    """ตรวจสอบว่าชุดข้อสอบผ่านเกณฑ์การกระจายระดับ Bloom หรือไม่."""
    total = len(analysis_results)
    if total == 0: 
        return {"pass": False, "reason": "ไม่มีข้อมูลข้อสอบ", "percentages": {}, "raw_counts": {}, "valid_total": 0} 

    # Standardized Level Names for grouping
    LEVEL_GROUPS = {
        "Remember": 0, "Understand": 0, "Apply": 0, 
        "Analyze": 0, "Evaluate": 0, "Create": 0, "Unknown": 0
    }
    
    for item in analysis_results:
        level = str(item.get("bloom_level", "")).strip().lower()
        if "remember" in level: LEVEL_GROUPS["Remember"] += 1
        elif "understand" in level: LEVEL_GROUPS["Understand"] += 1
        elif "apply" in level: LEVEL_GROUPS["Apply"] += 1
        elif "analyze" in level: LEVEL_GROUPS["Analyze"] += 1
        elif "evaluate" in level: LEVEL_GROUPS["Evaluate"] += 1
        elif "create" in level: LEVEL_GROUPS["Create"] += 1
        else: LEVEL_GROUPS["Unknown"] += 1

    apply_analyze_count = LEVEL_GROUPS["Apply"] + LEVEL_GROUPS["Analyze"]
    remember_understand_count = LEVEL_GROUPS["Remember"] + LEVEL_GROUPS["Understand"]
    evaluate_create_count = LEVEL_GROUPS["Evaluate"] + LEVEL_GROUPS["Create"]
    valid_total = total - LEVEL_GROUPS["Unknown"] # ข้อที่สามารถระบุระดับ Bloom ได้

    if valid_total == 0:
        return {"pass": False, "reason": "ไม่มีข้อสอบที่สามารถวิเคราะห์ระดับความคิดได้เลย", "percentages": {}, "raw_counts": LEVEL_GROUPS, "valid_total": 0} 
        
    percent = {
        "Remember/Understand": round((remember_understand_count / valid_total) * 100, 1) if valid_total > 0 else 0,
        "Apply/Analyze": round((apply_analyze_count / valid_total) * 100, 1) if valid_total > 0 else 0,
        "Evaluate/Create": round((evaluate_create_count / valid_total) * 100, 1) if valid_total > 0 else 0
    }

    # เกณฑ์ (ตัวอย่าง: ต่ำ ≤ 40%, กลาง ≥ 50%, สูง ≥ 10%)
    pass_r_u = percent["Remember/Understand"] <= 40
    pass_a_a = percent["Apply/Analyze"] >= 50
    pass_e_c = percent["Evaluate/Create"] >= 10
    passed = pass_r_u and pass_a_a and pass_e_c

    reason = "ชุดข้อสอบ **ผ่าน** เกณฑ์การกระจายระดับความคิด (Bloom)" if passed else "ชุดข้อสอบ **ไม่ผ่าน** เกณฑ์การกระจายระดับความคิด (Bloom)"

    return {
        "pass": passed,
        "reason": reason,
        "percentages": percent,
        "raw_counts": LEVEL_GROUPS,
        "valid_total": valid_total 
    }

def create_analysis_report(all_analysis, bloom_check):
    """สร้างข้อมูลสรุปและ DataFrame สำหรับการแสดงผล"""
    total_questions = len(all_analysis)
    
    failed_analysis = sum(1 for a in all_analysis if "QUOTA EXCEEDED" in a.get('improvement_suggestion', '') or "เกิดข้อผิดพลาดในการวิเคราะห์" in a.get('improvement_suggestion', ''))
    
    successfully_analyzed_questions = total_questions - failed_analysis
    good_questions = sum(1 for a in all_analysis if a.get('is_good_question') is True and a.get('bloom_level') != "ไม่สามารถระบุได้")

    summary_data = {
        "สถิติโดยรวม": {
            "จำนวนข้อสอบทั้งหมด": f"{total_questions} ข้อ",
            "ข้อสอบที่วิเคราะห์สำเร็จ": f"{successfully_analyzed_questions} ข้อ",
            "ข้อสอบ **ดี** (ใช้ได้เลย)": f"{good_questions} ข้อ ({round((good_questions/successfully_analyzed_questions)*100, 1) if successfully_analyzed_questions > 0 else 0}%)",
            "ข้อสอบ **ต้องปรับปรุง**": f"{successfully_analyzed_questions - good_questions} ข้อ ({round(((successfully_analyzed_questions - good_questions)/successfully_analyzed_questions)*100, 1) if successfully_analyzed_questions > 0 else 0}%)"
        },
        "การกระจายระดับความคิด": {
            "ผลลัพธ์โดยรวม": bloom_check['reason'],
            "ระดับความคิดต่ำ (จำ/เข้าใจ) (เป้าหมาย ≤ 40%)": f"{bloom_check['percentages'].get('Remember/Understand', 0)}%",
            "ระดับความคิดกลาง (ใช้/วิเคราะห์) (เป้าหมาย ≥ 50%)": f"{bloom_check['percentages'].get('Apply/Analyze', 0)}%", 
            "ระดับความคิดสูง (ประเมิน/สร้างสรรค์) (เป้าหมาย ≥ 10%)": f"{bloom_check['percentages'].get('Evaluate/Create', 0)}%",
            "ข้อที่ระบุระดับความคิดไม่ได้": f"{bloom_check['raw_counts'].get('Unknown', 0)} ข้อ",
            "raw_counts": bloom_check['raw_counts'],
            "valid_total": bloom_check.get('valid_total', 0)
        }
    }
    
    df_data = []
    for i, item in enumerate(all_analysis):
        is_good = "✅ ดี" if item.get('is_good_question') is True and item.get('bloom_level') != "ไม่สามารถระบุได้" else "❌ ปรับปรุง/ล้มเหลว"
        df_data.append({
            'ข้อที่': i + 1,
            'คุณภาพข้อสอบ': is_good,
            'ระดับความคิด': item.get('bloom_level', 'ไม่ระบุ'),
            'มาตรฐานหลักสูตร': item.get('curriculum_standard', 'ไม่ระบุ'),
            'คำตอบ': item.get('correct_option', 'ไม่ระบุ'),
            'เหตุผลโดยย่อ': item.get('reasoning', 'ไม่ระบุเหตุผล'),
            'ข้อเสนอแนะ': item.get('improvement_suggestion', 'ไม่มี'),
            'คำถามเต็ม': item.get('question_text', '')
        })
    df = pd.DataFrame(df_data)
    return summary_data, df

# --- 4. Main App Function (UI) ---

def run_app():
    # 🎨 ตั้งค่าหน้าจอ
    st.set_page_config(
        page_title="เครื่องมือวิเคราะห์ข้อสอบอัตโนมัติ (Gemini AI)",
        page_icon="📝", 
        layout="wide",
        initial_sidebar_state="auto", 
        menu_items=None
    )
    
    # 🎨 Custom CSS Theme - Premium Polished Design
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    
    /* ===== GLOBAL STYLES ===== */
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        font-family: 'Prompt', sans-serif;
        min-height: 100vh;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ===== SIDEBAR STYLES ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #475569;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #1e293b !important;
        font-weight: 600;
    }
    
    /* ===== MAIN CONTENT STYLES ===== */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1100px;
    }
    
    /* Main content area */
    .main > div {
        background: #ffffff;
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        text-align: center;
        padding: 0.5rem 0;
    }
    
    h2 {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
        padding-bottom: 0.75rem;
        margin-top: 1.5rem;
        border-bottom: 2px solid;
        border-image: linear-gradient(90deg, #6366f1, #a855f7, #e2e8f0) 1;
    }
    
    h3 {
        color: #334155 !important;
        font-weight: 600 !important;
    }
    
    /* Regular text */
    .stMarkdown, p, span, label {
        color: #475569 !important;
    }
    
    /* ===== CONTAINER & CARDS ===== */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.08);
        transition: all 0.3s ease;
        overflow: hidden;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
        border-color: #c7d2fe !important;
    }
    
    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] {
        background: transparent;
    }
    
    [data-testid="stFileUploader"] section {
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
        border: 2px dashed #a5b4fc;
        border-radius: 16px;
        transition: all 0.3s ease;
        padding: 2rem;
    }
    
    [data-testid="stFileUploader"] section:hover {
        border-color: #6366f1;
        background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.15);
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.8rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.4);
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
        box-shadow: 0 8px 35px rgba(139, 92, 246, 0.45);
    }
    
    /* ===== TEXT INPUT & TEXT AREA ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        color: #1e293b !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #94a3b8 !important;
    }
    
    /* ===== METRICS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
        border-radius: 16px;
        padding: 1.25rem;
        border: 1px solid #e0e7ff;
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.12);
        border-color: #c7d2fe;
    }
    
    [data-testid="stMetric"] label {
        color: #6366f1 !important;
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #10b981 !important;
        font-weight: 600;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: #f1f5f9;
        border-radius: 12px;
        padding: 0.35rem;
        gap: 0.35rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #64748b;
        border-radius: 10px;
        padding: 0.7rem 1.25rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
        color: #1e293b;
    }
    
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #6366f1 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        color: #1e293b !important;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: #f1f5f9;
        border-color: #c7d2fe;
    }
    
    .streamlit-expanderContent {
        background: #ffffff;
        border-radius: 0 0 12px 12px;
        border: 1px solid #e2e8f0;
        border-top: none;
    }
    
    /* ===== DATAFRAMES ===== */
    [data-testid="stDataFrame"] {
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    }
    
    /* ===== ALERTS ===== */
    .stSuccess {
        background: #f0fdf4 !important;
        border: 1px solid #86efac !important;
        border-radius: 12px;
        border-left: 4px solid #22c55e !important;
    }
    
    .stSuccess p, .stSuccess span {
        color: #166534 !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #fde68a !important;
        border-radius: 12px;
        border-left: 4px solid #f59e0b !important;
    }
    
    .stWarning p, .stWarning span {
        color: #92400e !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 1px solid #fecaca !important;
        border-radius: 12px;
        border-left: 4px solid #ef4444 !important;
    }
    
    .stError p, .stError span {
        color: #991b1b !important;
    }
    
    .stInfo {
        background: #eff6ff !important;
        border: 1px solid #bfdbfe !important;
        border-radius: 12px;
        border-left: 4px solid #6366f1 !important;
    }
    
    .stInfo p, .stInfo span {
        color: #1e3a8a !important;
    }
    
    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
        border-radius: 10px;
    }
    
    /* ===== STATUS ===== */
    [data-testid="stStatusWidget"] {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #c7d2fe, #e9d5ff, transparent);
        margin: 1.5rem 0;
    }
    
    /* ===== CODE BLOCKS ===== */
    .stCodeBlock {
        background: rgba(15, 23, 42, 0.95) !important;
        border-radius: 12px;
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* ===== CUSTOM SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #6366f1, #8b5cf6);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #8b5cf6, #a855f7);
    }
    
    /* ===== SPECIAL EFFECTS ===== */
    .floating-card {
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Language toggle function
    def toggle_language():
        if st.session_state.language == 'th':
            st.session_state.language = 'en'
        else:
            st.session_state.language = 'th'
    
    # Modern Minimal Header (Dynamic)
    st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 1.5rem 1rem 2rem 1rem;
        margin-bottom: 0.5rem;
    ">
        <h1 style="
            font-size: 2.4rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.75rem;
        ">
            {t('app_title')}
        </h1>
        <p style="
            color: #64748b;
            font-size: 1rem;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        ">
            {t('app_subtitle')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True) 

    
    with st.sidebar:
        # Language Toggle Button at top
        st.button(
            t('language_btn'), 
            on_click=toggle_language,
            use_container_width=True,
            key='lang_toggle'
        )
        st.markdown("---")
        
        st.header(t('sidebar_title'))
        
        if GEMINI_AVAILABLE:
            st.success(t('ai_connected'))
        else:
            st.error(t('ai_not_connected'))
        
        st.markdown(t('model_used'))
        st.info(f"{t('batch_analysis')}: `{GEMINI_BATCH_MODEL_NAME}`") 
        st.markdown("---")
        st.subheader(t('tips_title'))
        st.markdown(t('tip_1'))
        st.markdown(t('tip_2'))
        
        # Quota Warning
        st.markdown("---")
        st.warning(t('quota_warning'))

        if not GEMINI_AVAILABLE:
            st.error(t('api_warning'))

    # --- Custom Prompt Section (Main Content) ---
    st.markdown("---")
    with st.expander(t('custom_prompt_title'), expanded=False):
        st.markdown(f"**{t('custom_prompt_label')}**")
        custom_prompt_input = st.text_area(
            t('custom_prompt_label'),
            value=st.session_state.custom_prompt,
            height=150,
            placeholder=t('custom_prompt_placeholder'),
            key='custom_prompt_input',
            label_visibility="collapsed"
        )
        
        # Update session state
        if custom_prompt_input != st.session_state.custom_prompt:
            st.session_state.custom_prompt = custom_prompt_input
            st.session_state.analysis_results = None
        
        # Show status in columns
        col_status1, col_status2 = st.columns([1, 1])
        with col_status1:
            if st.session_state.custom_prompt.strip():
                st.success(t('custom_prompt_active'))
            else:
                st.info(t('custom_prompt_default'))

    # --- Step 1: Upload ---
    st.markdown("---")
    st.header(t('step1_title'))
    with st.container(border=True):
        st.markdown(f"**{t('file_uploader_label')}**")
        uploaded_file = st.file_uploader(
            t('file_uploader_label'), 
            type=['pdf', 'txt'], 
            accept_multiple_files=False, 
            key='file_uploader_widget', 
            label_visibility="collapsed"
        )
        st.caption(t('file_tip'))

        if uploaded_file is not None:
            # ตรวจสอบว่าไฟล์เปลี่ยนไปหรือไม่
            if uploaded_file.name != st.session_state.last_uploaded_file_name:
                st.session_state.analysis_results = None
                st.session_state.last_uploaded_file_name = uploaded_file.name
                st.session_state.question_texts = None
                
            if st.session_state.question_texts is None:
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                # Custom Loading UI สำหรับการสกัดข้อสอบ
                status_container = st.empty()
                status_container.info(f"{t('reading_file')}\n\n{t('from_file')} **{uploaded_file.name}**...")
                
                with st.spinner(t('extracting')):
                    try:
                        if file_extension == 'pdf':
                            with io.BytesIO(uploaded_file.getvalue()) as open_pdf_file:
                                pdf_reader = PdfReader(open_pdf_file)
                                raw_text = extract_text_from_pdf(pdf_reader)
                        elif file_extension == 'txt':
                            raw_text = uploaded_file.getvalue().decode("utf-8")
                        
                        question_texts = extract_questions(raw_text)
                        st.session_state.question_texts = question_texts
                        
                        status_container.empty() # ล้าง Custom Loading
                        
                        if not question_texts:
                            st.error(t('no_questions_found'))
                            st.info(t('file_tip'))
                            return 
                        
                    except Exception as e:
                        status_container.empty() # ล้าง Custom Loading
                        st.error(f"{t('file_read_error')} {e}")
                        return 
                
                # Rerun ครั้งเดียวหลังจากสกัดเสร็จ เพื่อแสดงผลลัพธ์
                st.rerun() 

            question_texts = st.session_state.question_texts
            if question_texts:
                st.success(t('extracted_questions').format(count=len(question_texts), filename=uploaded_file.name))
            


    # --- Step 2: Start Analysis ---
    st.markdown("---")
    st.header(t('step2_title'))
    
    # ใช้ Callback function เพื่อวิเคราะห์และบันทึกผลลัพธ์ (แก้ปัญหา Rerun ซ้ำซ้อน)
    def start_analysis_callback():
        if not GEMINI_AVAILABLE:
            st.error(t('api_not_ready'))
            return
            
        question_texts = st.session_state.question_texts
        analysis_results = []
        
        # ใช้ st.status เพื่อรวมสถานะทั้งหมด
        with st.status(t('starting_analysis'), expanded=True) as status_box:
            
            st.write(t('preparing_analysis').format(count=len(question_texts), model=GEMINI_BATCH_MODEL_NAME))
            progress_bar = st.progress(0, text=t('analysis_progress').format(current=0, total=len(question_texts)))
            
            for i, q_text in enumerate(question_texts):
                st.write(t('analyzing_question').format(num=i+1))
                analysis = analyze_with_gemini(q_text, question_id=i+1)
                analysis["question_text"] = q_text 
                analysis_results.append(analysis)
                
                progress_percent = (i + 1) / len(question_texts)
                progress_bar.progress(progress_percent, text=t('analysis_progress').format(current=i+1, total=len(question_texts)))
            
            # บันทึกผลลัพธ์ลงใน session state
            st.session_state.analysis_results = analysis_results
            
            # อัพเดทสถานะ
            status_box.update(label=t('analysis_complete'), state="complete", expanded=False)


    if st.session_state.question_texts and st.button(
        t('start_analysis_btn'), 
        type="primary", 
        use_container_width=True,
        on_click=start_analysis_callback 
    ):
        pass


    # --- Step 3: Report ---
    if st.session_state.analysis_results:
        st.divider()
        st.header(t('step3_title'))

        all_analysis = st.session_state.analysis_results
        successful_analysis = [a for a in all_analysis if a.get('bloom_level') != "ไม่สามารถระบุได้"]
        bloom_check = check_bloom_criteria(successful_analysis)
        summary_data, df = create_analysis_report(all_analysis, bloom_check)
        
        # ดึง valid_total ออกมาเพื่อใช้ในการคำนวณสัดส่วนในตาราง (แก้ NameError)
        valid_total = summary_data["การกระจายระดับความคิด"].get("valid_total", 0)

        # ใช้ Tabs สำหรับจัดระเบียบรายงาน
        # *** โค้ดที่แก้ไข: ลบ tab_raw ออกไป ***
        tab_summary, tab_details = st.tabs([t('tab_summary'), t('tab_details')])

        # --- Tab: Summary ---
        with tab_summary:
            st.subheader(t('summary_title'))
            stats = summary_data["สถิติโดยรวม"]
            col1, col2, col3, col4 = st.columns(4) 

            # Helper function to extract percent value
            def get_percent_delta(text):
                try: 
                    return text.split('(')[1].strip('%)') 
                except IndexError: 
                    return "0.0%"

            # Good Questions Metric
            good_count_str = stats["ข้อสอบ **ดี** (ใช้ได้เลย)"].split(' ')[0]
            good_percent_str = get_percent_delta(stats["ข้อสอบ **ดี** (ใช้ได้เลย)"])
            col1.metric(t('good_questions'), good_count_str, delta=f"{good_percent_str}%", delta_color="normal")
            
            # To Improve Metric
            improve_count_str = stats["ข้อสอบ **ต้องปรับปรุง**"].split(' ')[0]
            improve_percent_str = get_percent_delta(stats["ข้อสอบ **ต้องปรับปรุง**"])
            col2.metric(t('needs_improvement'), improve_count_str, delta=f"{improve_percent_str}%", delta_color="inverse")
            
            # Total Questions 
            col3.metric(t('total_questions'), stats["จำนวนข้อสอบทั้งหมด"].split(' ')[0])
            
            # Successfully Analyzed
            col4.metric(t('analyzed_success'), stats["ข้อสอบที่วิเคราะห์สำเร็จ"].split(' ')[0])
            
            st.markdown("---")
            st.subheader(t('bloom_criteria_title'))
            bloom_stats = summary_data["การกระจายระดับความคิด"]
            
            if bloom_check['pass']:
                st.success(f"**🎉 {bloom_stats['ผลลัพธ์โดยรวม']}**")
            else:
                st.warning(f"**❌ {bloom_stats['ผลลัพธ์โดยรวม']}**")
                
            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.metric(t('bloom_low'), bloom_stats["ระดับความคิดต่ำ (จำ/เข้าใจ) (เป้าหมาย ≤ 40%)"], delta=f"{t('target')} ≤ 40%")
            col_b2.metric(t('bloom_mid'), bloom_stats["ระดับความคิดกลาง (ใช้/วิเคราะห์) (เป้าหมาย ≥ 50%)"], delta=f"{t('target')} ≥ 50%")
            col_b3.metric(t('bloom_high'), bloom_stats["ระดับความคิดสูง (ประเมิน/สร้างสรรค์) (เป้าหมาย ≥ 10%)"], delta=f"{t('target')} ≥ 10%")
            
            st.markdown(f"{t('unidentified_bloom')} {bloom_stats['ข้อที่ระบุระดับความคิดไม่ได้']}")
            
            
            # --- สร้าง Pie Chart และ ตารางสรุป ---
            st.markdown("---")
            st.subheader(t('bloom_distribution'))
            
            col_chart, col_table = st.columns([1, 1.2]) 

            # 1. Pie Chart 
            with col_chart:
                bloom_counts = bloom_stats['raw_counts']
                # เตรียมข้อมูลสำหรับ Pie Chart (ไม่รวม Unknown)
                chart_data_raw = {
                    'ระดับ Bloom': list(bloom_counts.keys())[:-1],
                    'จำนวนข้อ': list(bloom_counts.values())[:-1],
                    'สี': [get_bloom_color(level) for level in list(bloom_counts.keys())[:-1]]
                }
                chart_df = pd.DataFrame(chart_data_raw)
                
                if not chart_df.empty and chart_df['จำนวนข้อ'].sum() > 0:
                    base = alt.Chart(chart_df).encode(
                        theta=alt.Theta("จำนวนข้อ", stack=True)
                    )
                    
                    pie = base.mark_arc(outerRadius=120).encode(
                        color=alt.Color("ระดับ Bloom", scale=alt.Scale(domain=chart_df['ระดับ Bloom'].tolist(), range=chart_df['สี'].tolist())),
                        order=alt.Order("จำนวนข้อ", sort="descending"),
                        tooltip=["ระดับ Bloom", "จำนวนข้อ"]
                    )
                    
                    st.altair_chart(pie, use_container_width=True)
                else:
                    st.warning("ไม่มีข้อมูลข้อสอบที่วิเคราะห์ระดับ Bloom ได้")
            
            # 2. ตารางสรุปคุณภาพ/จำนวนข้อตามระดับ Bloom
            with col_table:
                # สร้าง DataFrame สรุป
                summary_table_data = []
                for level, count in bloom_stats['raw_counts'].items():
                    if level == 'Unknown': continue 
                    
                    level_items = [a for a in all_analysis if level.lower() in a.get('bloom_level', '').lower()]
                    good_count = sum(1 for a in level_items if a.get('is_good_question') is True)
                    
                    percent_text = f"{round((count / valid_total) * 100, 1) if valid_total > 0 else 0}%"
                    
                    summary_table_data.append({
                        'ระดับ Bloom': level,
                        'จำนวนข้อ': count,
                        'สัดส่วน': percent_text,
                        'คุณภาพดี': good_count,
                        'ต้องปรับปรุง': count - good_count
                    })
                
                summary_table_df = pd.DataFrame(summary_table_data)
                
                st.markdown("**ตารางสรุปจำนวนและคุณภาพข้อสอบตามระดับ Bloom**")
                st.dataframe(
                    summary_table_df, 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={
                        'จำนวนข้อ': st.column_config.NumberColumn(format="%d ข้อ"),
                        'คุณภาพดี': st.column_config.NumberColumn(format="%d ข้อ"),
                        'ต้องปรับปรุง': st.column_config.NumberColumn(format="%d ข้อ"),
                    }
                )

        # --- Tab: Details ---
        with tab_details:
            st.subheader(t('details_title'))
            
            # 1. แสดง DataFrame สรุปก่อน
            st.dataframe(
                df[[
                    'ข้อที่', 'คุณภาพข้อสอบ', 'ระดับความคิด', 
                    'มาตรฐานหลักสูตร', 'คำตอบ', 'เหตุผลโดยย่อ', 
                    'ข้อเสนอแนะ'
                ]],
                column_config={
                    "คุณภาพข้อสอบ": st.column_config.Column("คุณภาพข้อสอบ", width="small"),
                    "ระดับความคิด": st.column_config.Column("ระดับความคิด", width="small"),
                    "เหตุผลโดยย่อ": st.column_config.Column("เหตุผลโดยย่อ", width="medium"),
                },
                use_container_width=True,
                hide_index=True
            )
            
            # 2. Loop สร้าง expander สำหรับทุกข้อ
            st.markdown("---")
            st.markdown(t('click_detail'))
            
            for q_index, item in enumerate(all_analysis):
                quality_status = t('good') if item.get('is_good_question') is True and item.get('bloom_level') != "ไม่สามารถระบุได้" else t('improve')
                expander_title = f"**{t('question_num')} {q_index+1}** | {quality_status} | {t('bloom_level')}: **{item.get('bloom_level', 'ไม่ระบุ')}**"
                
                # ใช้ st.expander เพื่อแสดงรายละเอียด
                with st.expander(expander_title):
                    
                    st.markdown(t('full_question'))
                    st.code(item.get('question_text', 'N/A'), language='markdown')
                    
                    st.markdown("---")

                    # การแสดงผลแบบชิดและมีสีสันสวยงาม 
                    bloom_color = get_bloom_color(item.get('bloom_level', 'ไม่ระบุ'))
                    text_color = get_text_color_for_bloom(item.get('bloom_level', 'ไม่ระบุ'))
                    
                    col_det1, col_det2, col_det3 = st.columns([1, 1, 1]) 

                    with col_det1:
                        # แสดง Bloom Level
                        st.markdown(
                            f"""
                            <div style='background-color:{bloom_color}; color:{text_color}; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;'>
                                <strong>💡 ระดับ Bloom:</strong> {item.get('bloom_level', 'N/A')}
                            </div>
                            """, unsafe_allow_html=True
                        )
                    
                    with col_det2:
                         # แสดง Difficulty (พร้อมแก้ไขสีตัวอักษร)
                        difficulty_level = item.get('difficulty', 'ไม่ระบุ')
                        difficulty_color = {"ง่าย": "#008000", "ปานกลาง": "#FFA500", "ยาก": "#FF4500"}.get(difficulty_level, "#808080")
                        
                        # กำหนดสีตัวอักษรตามพื้นหลัง
                        if difficulty_level in ["ปานกลาง"]: 
                            difficulty_text_color = "white" 
                        else:
                            difficulty_text_color = "white"
                        
                        st.markdown(
                            f"""
                            <div style='background-color:{difficulty_color}; color:{difficulty_text_color}; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;'>
                                <strong>{t('difficulty')}</strong> {difficulty_level}
                            </div>
                            """, unsafe_allow_html=True
                        )

                    with col_det3:
                        # แสดง Correct Option
                        st.markdown(
                            f"""
                            <div style='background-color:#0077B6; color:white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;'>
                                <strong>{t('correct_answer')}</strong> {item.get('correct_option', 'N/A')}
                            </div>
                            """, unsafe_allow_html=True
                        )

                    # ข้อมูลหลัก 
                    st.markdown(f"{t('curriculum_indicator')} `{item.get('curriculum_standard', 'N/A')}`")
                    st.markdown(f"{t('bloom_reason')} {item.get('reasoning', 'N/A')}")
                    
                    st.divider()
                    st.subheader(t('answer_analysis_title'))
                    st.markdown(f"{t('correct_analysis')} {item.get('correct_option_analysis', 'N/A')}")
                    st.markdown(f"{t('distractor_analysis')} {item.get('distractor_analysis', 'N/A')}")
                    st.markdown(f"{t('why_good_distractor')} {item.get('why_good_distractor', 'N/A')}")
                    
                    st.warning(f"{t('improvement_suggestion')} {item.get('improvement_suggestion', 'N/A')}")
                
                st.divider() 


        # --- Tab: Raw JSON ---
        # (ส่วนนี้ถูกลบตามคำขอของผู้ใช้)


if __name__ == "__main__":
    run_app()