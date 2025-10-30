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
            "difficulty": "ไม่เมิน", "curriculum_standard": "ไม่ระบุ",
            "correct_option": "ไม่ระบุ", "correct_option_analysis": "ไม่มีการเชื่อมต่อ AI",
            "distractor_analysis": "ไม่มีการเชื่อมต่อ AI", "why_good_distractor": "ไม่มีการเชื่อมต่อ AI",
            "is_good_question": False, "improvement_suggestion": "ไม่สามารถวิเคราะห์ได้: ไม่พบ API Key"
        } 

    model = genai.GenerativeModel(
        GEMINI_BATCH_MODEL_NAME, 
        system_instruction=SYSTEM_INSTRUCTION_PROMPT
    )
    
    question_text_formatted = f"คำถามข้อที่ {question_id}:\n{question_text}"
    
    # การจัดรูปแบบ Prompt ที่ถูกต้อง
    full_prompt = FEW_SHOT_PROMPT_TEMPLATE.format(user_query=question_text_formatted) 
    
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
            
            if "429" in str(e) or "quota" in str(e).lower():
                last_error_message = f"QUOTA EXCEEDED: คุณใช้โควต้า {GEMINI_BATCH_MODEL_NAME} ครบแล้ว ({e})"
                break
            
            continue # ลองใหม่ (Retry)

    # Fallback สุดท้าย: หาก AI วิเคราะห์ไม่ได้เลย
    return {
        "bloom_level": "ไม่สามารถระบุได้", "reasoning": "AI วิเคราะห์ล้มเหลว",
        "difficulty": "ไม่สามารถประเมินได้", "curriculum_standard": "ไม่สามารถระบุได้",
        "correct_option": "ไม่ระบุ", "correct_option_analysis": "ไม่ระบุ",
        "distractor_analysis": "ไม่ระบุ", "why_good_distractor": "ไม่ระบุ",
        "is_good_question": False, 
        "improvement_suggestion": f"**เกิดข้อผิดพลาดในการวิเคราะห์** (วิเคราะห์ไม่ได้ 3 ครั้ง): {last_error_message}"
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
    
    st.title("เครื่องมือวิเคราะห์คุณภาพข้อสอบอัตโนมัติ 🤖✨") 
    st.markdown(
        """
        แพลตฟอร์มนี้ใช้ **Gemini AI** ในการวิเคราะห์ข้อสอบปรนัยภาษาไทยตามหลักสูตรแกนกลางฯ
        พร้อมประเมินระดับความคิดตาม **Bloom’s Taxonomy** และคุณภาพของข้อสอบ.
        """
    )
    st.markdown("---") 

    
    with st.sidebar:
        st.header("⚙️ การตั้งค่า & สถานะ AI")
        
        if GEMINI_AVAILABLE:
            st.success("✅ เชื่อมต่อ AI สำเร็จ")
        else:
            st.error("❌ ไม่พบ API Key (GEMINI_API_KEY) - กรุณาตั้งค่าใน `.env`")
        
        st.markdown("**โมเดลที่ใช้งาน**")
        st.info(f"Batch Analysis: `{GEMINI_BATCH_MODEL_NAME}`") 
        st.markdown("---")
        st.subheader("💡 เคล็ดลับ")
        st.markdown("- ใช้ไฟล์ **PDF** หรือ **TXT**")
        st.markdown("- ข้อสอบควรมี **เลขข้อ** (เช่น 1., 2.) และ **ตัวเลือก** (เช่น ก., ข.)")

        if not GEMINI_AVAILABLE:
            st.warning("โปรดทราบ: คุณต้องตั้งค่า GEMINI_API_KEY ในไฟล์ .env เพื่อใช้งานส่วนวิเคราะห์")

    # --- Step 1: Upload ---
    st.header("1️⃣ อัปโหลดไฟล์ข้อสอบ (Batch Analysis)")
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "📁 เลือกไฟล์ข้อสอบ **(.PDF หรือ .TXT)**", 
            type=['pdf', 'txt'], 
            accept_multiple_files=False, 
            key='file_uploader_widget', 
            label_visibility="collapsed"
        )

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
                status_container.info(f"⏳ **กำลังอ่านและสกัดข้อสอบ:**\n\nจากไฟล์ **{uploaded_file.name}**...")
                
                with st.spinner("กำลังสกัดข้อความ..."):
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
                            st.error("❌ **ไม่พบข้อสอบ** กรุณาตรวจสอบรูปแบบไฟล์ (ไม่มีเลขข้อ/ตัวเลือก หรือรูปแบบซับซ้อนเกินไป)")
                            st.info("💡 **เคล็ดลับการเตรียมไฟล์:** ไฟล์ควรมี **เลขข้อ** ที่ชัดเจน (เช่น 1., 2., 3.) และมี **ตัวเลือก** (เช่น ก., ข., ค., ง.)")
                            return 
                        
                    except Exception as e:
                        status_container.empty() # ล้าง Custom Loading
                        st.error(f"❌ **เกิดข้อผิดพลาดในการอ่านไฟล์:** {e}")
                        return 
                
                # Rerun ครั้งเดียวหลังจากสกัดเสร็จ เพื่อแสดงผลลัพธ์
                st.rerun() 

            question_texts = st.session_state.question_texts
            if question_texts:
                st.success(f"✅ สกัดข้อสอบได้แล้ว **{len(question_texts)} ข้อ** จากไฟล์ `{uploaded_file.name}`")
            


    # --- Step 2: Start Analysis ---
    st.markdown("---")
    st.header("2️⃣ เริ่มต้นวิเคราะห์และสร้างรายงาน 🚀")
    
    # ใช้ Callback function เพื่อวิเคราะห์และบันทึกผลลัพธ์ (แก้ปัญหา Rerun ซ้ำซ้อน)
    def start_analysis_callback():
        if not GEMINI_AVAILABLE:
            st.error("Key ไม่พร้อมใช้งาน กรุณาตรวจสอบการตั้งค่า")
            return
            
        question_texts = st.session_state.question_texts
        analysis_results = []
        
        # ใช้ st.status เพื่อรวมสถานะทั้งหมด
        with st.status("🚀 **กำลังเริ่มการวิเคราะห์ด้วย AI...**", expanded=True) as status_box:
            
            st.write(f"⏳ กำลังเตรียมวิเคราะห์ข้อสอบ {len(question_texts)} ข้อ โดยใช้ `{GEMINI_BATCH_MODEL_NAME}`")
            progress_bar = st.progress(0, text=f"กำลังวิเคราะห์ข้อสอบ 0/{len(question_texts)} ข้อ...")
            
            for i, q_text in enumerate(question_texts):
                st.write(f"🤖 วิเคราะห์ข้อที่ {i+1}...")
                analysis = analyze_with_gemini(q_text, question_id=i+1)
                analysis["question_text"] = q_text 
                analysis_results.append(analysis)
                
                progress_percent = (i + 1) / len(question_texts)
                progress_bar.progress(progress_percent, text=f"กำลังวิเคราะห์ข้อสอบ {i+1}/{len(question_texts)} ข้อ...")
            
            # บันทึกผลลัพธ์ลงใน session state
            st.session_state.analysis_results = analysis_results
            
            # อัพเดทสถานะ
            status_box.update(label="🎉 **การวิเคราะห์เสร็จสมบูรณ์!**", state="complete", expanded=False)


    if st.session_state.question_texts and st.button(
        "🚀 **กดที่นี่เพื่อเริ่มการวิเคราะห์ด้วย AI**", 
        type="primary", 
        use_container_width=True,
        on_click=start_analysis_callback 
    ):
        pass


    # --- Step 3: Report ---
    if st.session_state.analysis_results:
        st.divider()
        st.header("3️⃣ ผลการวิเคราะห์ชุดข้อสอบ 📝")

        all_analysis = st.session_state.analysis_results
        successful_analysis = [a for a in all_analysis if a.get('bloom_level') != "ไม่สามารถระบุได้"]
        bloom_check = check_bloom_criteria(successful_analysis)
        summary_data, df = create_analysis_report(all_analysis, bloom_check)
        
        # ดึง valid_total ออกมาเพื่อใช้ในการคำนวณสัดส่วนในตาราง (แก้ NameError)
        valid_total = summary_data["การกระจายระดับความคิด"].get("valid_total", 0)

        # ใช้ Tabs สำหรับจัดระเบียบรายงาน
        # *** โค้ดที่แก้ไข: ลบ tab_raw ออกไป ***
        tab_summary, tab_details = st.tabs(["📊 สรุปรายงาน & เกณฑ์ Bloom", "📝 รายละเอียดรายข้อ"])

        # --- Tab: Summary ---
        with tab_summary:
            st.subheader("📊 สรุปภาพรวมคุณภาพข้อสอบ")
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
            col1.metric("✅ ข้อสอบคุณภาพดี", good_count_str, delta=f"{good_percent_str}%", delta_color="normal")
            
            # To Improve Metric
            improve_count_str = stats["ข้อสอบ **ต้องปรับปรุง**"].split(' ')[0]
            improve_percent_str = get_percent_delta(stats["ข้อสอบ **ต้องปรับปรุง**"])
            col2.metric("⚠️ ข้อสอบต้องปรับปรุง", improve_count_str, delta=f"{improve_percent_str}%", delta_color="inverse")
            
            # Total Questions 
            col3.metric("📝 จำนวนข้อสอบทั้งหมด", stats["จำนวนข้อสอบทั้งหมด"].split(' ')[0])
            
            # Successfully Analyzed
            col4.metric("🤖 วิเคราะห์สำเร็จ", stats["ข้อสอบที่วิเคราะห์สำเร็จ"].split(' ')[0])
            
            st.markdown("---")
            st.subheader("💡 เกณฑ์การกระจายระดับความคิด (Bloom)")
            bloom_stats = summary_data["การกระจายระดับความคิด"]
            
            if bloom_check['pass']:
                st.success(f"**🎉 {bloom_stats['ผลลัพธ์โดยรวม']}**")
            else:
                st.warning(f"**❌ {bloom_stats['ผลลัพธ์โดยรวม']}**")
                
            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.metric("ระดับความคิดต่ำ (จำ/เข้าใจ)", bloom_stats["ระดับความคิดต่ำ (จำ/เข้าใจ) (เป้าหมาย ≤ 40%)"], delta="เป้าหมาย ≤ 40%")
            col_b2.metric("ระดับความคิดกลาง (ใช้/วิเคราะห์)", bloom_stats["ระดับความคิดกลาง (ใช้/วิเคราะห์) (เป้าหมาย ≥ 50%)"], delta="เป้าหมาย ≥ 50%")
            col_b3.metric("ระดับความคิดสูง (ประเมิน/สร้างสรรค์)", bloom_stats["ระดับความคิดสูง (ประเมิน/สร้างสรรค์) (เป้าหมาย ≥ 10%)"], delta="เป้าหมาย ≥ 10%")
            
            st.markdown(f"**ข้อที่ระบุระดับความคิดไม่ได้:** {bloom_stats['ข้อที่ระบุระดับความคิดไม่ได้']}")
            
            
            # --- สร้าง Pie Chart และ ตารางสรุป ---
            st.markdown("---")
            st.subheader("📈 การกระจายระดับ Bloom’s Taxonomy")
            
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
            st.subheader("📝 รายละเอียดผลการวิเคราะห์รายข้อ")
            
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
            st.markdown("### 🔎 คลิกดูรายละเอียดการวิเคราะห์ (10 Fields) รายข้อ")
            
            for q_index, item in enumerate(all_analysis):
                quality_status = "✅ คุณภาพดี" if item.get('is_good_question') is True and item.get('bloom_level') != "ไม่สามารถระบุได้" else "❌ ต้องปรับปรุง/ล้มเหลว"
                expander_title = f"**ข้อที่ {q_index+1}** | {quality_status} | ระดับความคิด: **{item.get('bloom_level', 'ไม่ระบุ')}**"
                
                # ใช้ st.expander เพื่อแสดงรายละเอียด
                with st.expander(expander_title):
                    
                    st.markdown(f"**คำถามเต็ม:**")
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
                                <strong>⚖️ ความยาก:</strong> {difficulty_level}
                            </div>
                            """, unsafe_allow_html=True
                        )

                    with col_det3:
                        # แสดง Correct Option
                        st.markdown(
                            f"""
                            <div style='background-color:#0077B6; color:white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px;'>
                                <strong>✅ คำตอบ:</strong> {item.get('correct_option', 'N/A')}
                            </div>
                            """, unsafe_allow_html=True
                        )

                    # ข้อมูลหลัก 
                    st.markdown(f"**📚 ตัวชี้วัดหลักสูตร:** `{item.get('curriculum_standard', 'N/A')}`")
                    st.markdown(f"**🧠 เหตุผลของระดับ Bloom/คุณภาพ:** {item.get('reasoning', 'N/A')}")
                    
                    st.divider()
                    st.subheader("วิเคราะห์คำตอบและตัวลวง")
                    st.markdown(f"**✅ วิเคราะห์คำตอบที่ถูก:** {item.get('correct_option_analysis', 'N/A')}")
                    st.markdown(f"**❌ วิเคราะห์ตัวเลือกลวง (Distractors):** {item.get('distractor_analysis', 'N/A')}")
                    st.markdown(f"**💡 เหตุผลที่ตัวลวงดี:** {item.get('why_good_distractor', 'N/A')}")
                    
                    st.warning(f"**🔧 ข้อเสนอแนะในการปรับปรุง:** {item.get('improvement_suggestion', 'N/A')}")
                
                st.divider() 


        # --- Tab: Raw JSON ---
        # (ส่วนนี้ถูกลบตามคำขอของผู้ใช้)


if __name__ == "__main__":
    run_app()