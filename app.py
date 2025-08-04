# math_exam_analyzer_bloom.py

import streamlit as st
from PyPDF2 import PdfReader
import re
import tempfile
import os

# ✅ ส่วน OCR
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    st.warning("⚠️ ระบบ OCR ไม่พร้อมใช้งาน (ต้องติดตั้ง pytesseract และ pdf2image)")

# ✅ Configuration - ปรับให้เหมาะสมกับเครื่องของคุณ
if OCR_AVAILABLE:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe" # ปรับ path ให้ตรงกับที่ติดตั้ง Tesseract บนเครื่องคุณ
    POPPLER_PATH = r"C:\Users\LOQ\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"    # ปรับ path ให้ตรงกับที่ติดตั้ง Poppler บนเครื่องคุณ

st.set_page_config(
    page_title="ตรวจสอบมาตรฐานข้อสอบคณิตศาสตร์ ม.4",
    page_icon="📐",
    layout="wide"
)

# 🔥 CSS ปรับแต่งหน้าตาให้สวยงาม
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        color: #2c3e50;
        text-align: center;
        padding: 1rem;
    }
    .result-box {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    .success {
        border-left: 5px solid #27ae60;
    }
    .warning {
        border-left: 5px solid #f39c12;
    }
    .error {
        border-left: 5px solid #e74c3c;
    }
    .info {
        border-left: 5px solid #3498db;
    }
    /* เพิ่ม CSS สำหรับระดับความยาก */
    .difficulty-summary {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 10px;
        margin: 20px 0;
    }
    .difficulty-item {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 5px rgba(0,0,0,0.1);
        flex: 1;
        min-width: 120px;
    }
    .difficulty-easy { border-top: 4px solid #28a745; }
    .difficulty-medium { border-top: 4px solid #ffc107; }
    .difficulty-hard { border-top: 4px solid #dc3545; }
    .overall-difficulty {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        font-size: 1.2em;
        font-weight: bold;
    }
    .difficulty-easy-bg { background-color: #d4edda; color: #155724; }
    .difficulty-medium-bg { background-color: #fff3cd; color: #856404; }
    .difficulty-hard-bg { background-color: #f8d7da; color: #721c24; }
    .difficulty-mixed-bg { background-color: #d1ecf1; color: #0c5460; }
    /* CSS สำหรับคำแนะนำ */
    .improvement-suggestion {
        background-color: #e7f3ff;
        border-left: 4px solid #3498db;
        padding: 10px;
        margin: 10px 0;
        border-radius: 0 4px 4px 0;
    }
    /* CSS สำหรับ Bloom's */
    .bloom-level {
        background-color: #fff8e1;
        border-left: 4px solid #ffc107;
        padding: 5px;
        margin: 5px 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>📐 ตรวจสอบมาตรฐานข้อสอบคณิตศาสตร์ ม.4 (ตาม Bloom's Taxonomy)</h1>", unsafe_allow_html=True)

# 🔹 กำหนดเกณฑ์มาตรฐานใน sidebar
# ใช้ st.session_state เพื่อจัดการค่าที่ผู้ใช้ตั้งไว้
if 'min_questions' not in st.session_state:
    st.session_state.min_questions = 10
if 'min_choices' not in st.session_state:
    st.session_state.min_choices = 5

with st.sidebar:
    st.header("⚙️ ตั้งค่าเกณฑ์มาตรฐาน")
    # อ่านค่าจาก session_state และอัปเดตเมื่อผู้ใช้เปลี่ยน
    st.session_state.min_questions = st.number_input("📌 จำนวนข้อสอบขั้นต่ำ", value=st.session_state.min_questions, min_value=1, step=1, key="min_q_input")
    st.session_state.min_choices = st.number_input("📌 จำนวนข้อที่ต้องมีตัวเลือก", value=st.session_state.min_choices, min_value=1, step=1, key="min_c_input")
    st.divider()
    st.info("💡 เคล็ดลับ: ระบบจะตรวจทั้งจาก PDF และ OCR หาก PDF ไม่มีข้อความ")

uploaded_file = st.file_uploader("📎 อัพโหลดไฟล์ PDF (คณิตศาสตร์ ม.4)", type=["pdf"], key="pdf_uploader")

# --- เพิ่มข้อมูล Bloom's Taxonomy สำหรับคณิตศาสตร์ ม.4 ---
BLOOMS_TAXONOMY_MATH_M4 = {
    "Remembering": {
        "keywords": ["จำ", "บอก", "แสดง", "เขียน", "แทน", "คือ", "มีชื่อว่า", "ใช้สัญลักษณ์", "สมบัติ", "ความหมาย", "นิยาม"],
        "verbs": ["จำ", "บอก", "แสดง", "เขียน", "แทน", "ระบุ", "เลือก", "จับคู่", "เรียก", "ยกตัวอย่าง"],
        "patterns": [r"คืออะไร\?", r"มีชื่อว่าอะไร\?", r"จงแสดง.*สัญลักษณ์", r"จงเขียน.*ในรูป.*", r"สมบัติ.*คือ.*", r"นิยาม.*คือ.*"]
    },
    "Understanding": {
        "keywords": ["อธิบาย", "สรุป", "ตีความ", "แปลงรูป", "แสดงวิธี", "เหตุผล", "เพราะ", "ต่างจาก", "เหมือน"],
        "verbs": ["อธิบาย", "สรุป", "ตีความ", "แปลงรูป", "แสดง", "เข้าใจ", "เปรียบเทียบ", "สรุปใจความ"],
        "patterns": [r"จงอธิบาย.*", r"จงตีความ.*", r"จงสรุป.*", r"ทำไม.*", r"จงเปรียบเทียบ.*"]
    },
    "Applying": {
        "keywords": ["คำนวณ", "แก้", "หา", "แทนค่า", "ใช้", "วิเคราะห์กรณี", "แก้สมการ", "หาค่า", "ประยุกต์"],
        "verbs": ["คำนวณ", "แก้", "หา", "วิเคราะห์", "เปรียบเทียบ", "แปลง", "แทนค่า", "จัดรูป", "พิสูจน์(ง่าย)", "ใช้", "ประยุกต์"],
        "patterns": [r"จงหา.*", r"จงคำนวณ.*", r"แก้สมการ.*", r"จงแทนค่า.*", r"จงใช้.*", r"จงประยุกต์.*"]
    },
    "Analyzing": {
        "keywords": ["วิเคราะห์", "เปรียบเทียบ", "จำแนกประเภท", "ตรวจสอบ", "หาความสัมพันธ์", "แยกแยะ", "ผิดพลาด", "ข้อผิด"],
        "verbs": ["วิเคราะห์", "เปรียบเทียบ", "จำแนก", "ตรวจสอบ", "หาความสัมพันธ์", "แยกแยะ", "วินิจฉัย"],
        "patterns": [r"จงวิเคราะห์.*", r"เปรียบเทียบ.*", r"ตรวจสอบ.*ว่า.*", r"จงหาความสัมพันธ์.*", r"จงวินิจฉัย.*"]
    },
    "Evaluating": {
        "keywords": ["ประเมิน", "ตัดสิน", "ตรวจสอบ", "ให้เหตุผล", "วิจารณ์", "พิสูจน์", "ดีกว่า", "ถูกต้องหรือไม่", "เหตุใด"],
        "verbs": ["ประเมิน", "ตัดสิน", "ตรวจสอบ", "ให้เหตุผล", "วิจารณ์", "พิสูจน์", "ตัดสินคุณค่า"],
        "patterns": [r"จงพิสูจน์.*", r"จงให้เหตุผล.*", r"ตรวจสอบว่า.*", r"ประเมิน.*ว่า.*", r"จงตัดสิน.*", r".*ถูกต้องหรือไม่\?*"]
    },
    "Creating": {
        "keywords": ["ออกแบบ", "สร้าง", "วางแผน", "ประดิษฐ์", "หาวิธีใหม่", "ตั้งโจทย์", "เสนอ", "ประดิษฐ์"],
        "verbs": ["ออกแบบ", "สร้าง", "วางแผน", "ประดิษฐ์", "หาวิธี", "ตั้งโจทย์", "เสนอ", "ประดิษฐ์", "จัดทำ"],
        "patterns": [r"จงออกแบบ.*", r"จงสร้าง.*", r"จงตั้งโจทย์.*", r"จงเสนอ.*", r"จงประดิษฐ์.*"]
    }
}

def analyze_bloom_level_math_m4(question_text, choices_list):
    """
    วิเคราะห์ระดับ Bloom's Taxonomy สำหรับคำถามคณิตศาสตร์ ม.4
    """
    # แปลงเป็นตัวพิมพ์เล็กเพื่อความง่ายในการค้นหา
    text_lower = question_text.lower()
    found_levels = []

    # ตรวจสอบแต่ละระดับ
    for level, criteria in BLOOMS_TAXONOMY_MATH_M4.items():
        keywords = criteria["keywords"]
        verbs = criteria["verbs"]
        patterns = criteria["patterns"]

        # ถ้าพบคำสำคัญหรือรูปแบบของระดับนี้
        if (any(kw in text_lower for kw in keywords) or
            any(v in text_lower for v in verbs) or
            any(re.search(pat, text_lower) for pat in patterns)):
            found_levels.append(level)

    # กำหนดลำดับความสำคัญ: Creating > Evaluating > Analyzing > Applying > Understanding > Remembering
    priority_order = ["Creating", "Evaluating", "Analyzing", "Applying", "Understanding", "Remembering"]
    for level in priority_order:
        if level in found_levels:
            # จัดระดับความยากตาม Bloom's
            if level in ["Remembering", "Understanding"]:
                difficulty = "ง่าย"
            elif level in ["Applying", "Analyzing"]:
                difficulty = "ปานกลาง"
            else: # Creating, Evaluating
                difficulty = "ยาก"
            return difficulty, level, found_levels # คืนค่าระดับความยาก, ระดับ Bloom ที่พบ, รายการที่พบทั้งหมด

    # ถ้าไม่พบในเกณฑ์ Bloom's ให้ fallback ไปใช้เกณฑ์เดิม
    word_count = len(question_text.split())
    choice_count = len(choices_list)
    negative_words = ['ไม่', 'ไม่ใช่', 'ผิด', 'ยกเว้น', 'นอกจาก']
    has_negative_word = any(word in question_text for word in negative_words)
    
    if word_count <= 8 and choice_count >= 4 and not has_negative_word:
        difficulty = 'ง่าย'
    elif word_count <= 15 and choice_count >= 4:
        difficulty = 'ปานกลาง'
    else:
        difficulty = 'ยาก'
        
    reasons_fallback = []
    if word_count <= 8:
        reasons_fallback.append("คำถามสั้น")
    elif word_count > 15:
        reasons_fallback.append("คำถามยาว")
    else:
        reasons_fallback.append("คำถามมีความยาวปานกลาง")

    if choice_count >= 4:
        reasons_fallback.append("มีตัวเลือกครบ 4 ข้อ")
    else:
        reasons_fallback.append(f"ตัวเลือกน้อย ({choice_count} ข้อ)")

    if has_negative_word:
        reasons_fallback.append("มีคำปฏิเสธ เช่น 'ไม่', 'ไม่ใช่', 'ผิด'")
    else:
        reasons_fallback.append("ไม่มีคำปฏิเสธ")
        
    return difficulty, "ไม่พบ (Fallback)", reasons_fallback

def analyze_exam_detailed(text):
    """วิเคราะห์ข้อสอบแบบละเอียด พร้อมวิเคราะห์ระดับความยากตาม Bloom's"""
    lines = text.splitlines()
    questions = []
    current_question = None
    question_count = 0
    choice_count = 0

    # ปรับปรุง regex ให้แม่นยำขึ้น
    question_pattern = re.compile(r'^\s*(?:ข้อ\W*\d+|ข้อที่\W*\d+|\d+\.)\s*', re.IGNORECASE)
    choice_pattern = re.compile(r'^\s*[\(\[\{]?\s*[ก-ฮ๐-๙]\s*[\.|\)]|^\s*[\(\[\{]?\s*\d+\s*[\.|\)]')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # ตรวจหาคำถาม
        if question_pattern.match(line):
            question_count += 1
            current_question = {
                'number': question_count,
                'text': line,
                'choices': [],
                'line_number': i
            }
            questions.append(current_question)

        # ตรวจหาตัวเลือก (เฉพาะเมื่อมีคำถามอยู่)
        elif current_question and choice_pattern.match(line):
            current_question['choices'].append(line)
            choice_count += 1

    # นับคำถามที่มีตัวเลือก
    questions_with_choices = sum(1 for q in questions if len(q['choices']) > 0)

    # เพิ่มการวิเคราะห์ระดับความยากตาม Bloom's ให้แต่ละคำถาม
    easy_count = 0
    medium_count = 0
    hard_count = 0

    for question in questions:
        difficulty_level, bloom_level, bloom_indicators = analyze_bloom_level_math_m4(question['text'], question['choices'])
        question['difficulty'] = difficulty_level
        question['bloom_level'] = bloom_level
        question['bloom_indicators'] = bloom_indicators

        # นับจำนวนตามระดับความยาก
        if difficulty_level == 'ง่าย':
            easy_count += 1
        elif difficulty_level == 'ปานกลาง':
            medium_count += 1
        else:
            hard_count += 1

    return {
        'total_questions': question_count,
        'total_choices': choice_count,
        'questions_with_choices': questions_with_choices,
        'questions': questions,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count
    }


def extract_text_from_pdf(pdf_reader):
    """ดึงข้อความจาก PDF แบบละเอียด"""
    text = ""
    for page_num, page in enumerate(pdf_reader.pages):
        try:
            extracted = page.extract_text()
            if extracted and extracted.strip():
                text += f"\n--- หน้า {page_num + 1} ---\n"
                text += extracted + "\n"
        except Exception as e:
            st.warning(f"ไม่สามารถดึงข้อความจากหน้า {page_num + 1}: {str(e)}")
    return text

def ocr_pdf_pages(file_path, dpi=300):
    """OCR PDF ทีละหน้าด้วย DPI สูง"""
    if not OCR_AVAILABLE:
        return ""
    try:
        images = convert_from_path(
            file_path,
            poppler_path=POPPLER_PATH,
            dpi=dpi,
            grayscale=True  # ช่วยเพิ่มความแม่นยำของ OCR
        )
        text = ""
        for i, image in enumerate(images):
            # ปรับภาพให้คมชัดขึ้นสำหรับ OCR
            image = image.convert('L')  # grayscale
            page_text = pytesseract.image_to_string(image, lang="tha+eng")
            if page_text.strip():
                text += f"\n--- หน้า OCR {i + 1} ---\n"
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการ OCR: {str(e)}")
        return ""

def validate_system_requirements():
    """ตรวจสอบว่าระบบมีการติดตั้งทุกอย่างครบถ้วน"""
    errors = []
    if not OCR_AVAILABLE:
        errors.append("ไม่พบ pytesseract หรือ pdf2image")
        return errors

    # ตรวจสอบ Tesseract
    try:
        if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
            errors.append("ไม่พบ Tesseract-OCR ที่ path ที่ระบุ")
    except:
        errors.append("ไม่สามารถตรวจสอบ Tesseract ได้")

    # ตรวจสอบ Poppler
    try:
        if POPPLER_PATH and not os.path.exists(POPPLER_PATH):
            errors.append("ไม่พบ Poppler ที่ path ที่ระบุ")
    except:
        errors.append("ไม่สามารถตรวจสอบ Poppler ได้")
    return errors

def display_difficulty_analysis(analysis_result):
    """แสดงผลการวิเคราะห์ระดับความยาก"""
    total = analysis_result['total_questions']
    if total == 0:
        return

    easy_count = analysis_result['easy_count']
    medium_count = analysis_result['medium_count']
    hard_count = analysis_result['hard_count']

    easy_pct = (easy_count / total) * 100
    medium_pct = (medium_count / total) * 100
    hard_pct = (hard_count / total) * 100

    # กำหนดระดับความยากโดยรวม
    if easy_pct >= 70:
        overall_difficulty = "ง่าย"
        difficulty_class = "difficulty-easy-bg"
        emoji = "🟢"
    elif hard_pct >= 50:
        overall_difficulty = "ยาก"
        difficulty_class = "difficulty-hard-bg"
        emoji = "🔴"
    elif medium_pct >= 50:
        overall_difficulty = "ปานกลาง"
        difficulty_class = "difficulty-medium-bg"
        emoji = "🟡"
    else:
        overall_difficulty = "หลากหลาย"
        difficulty_class = "difficulty-mixed-bg"
        emoji = "🟣"

    # แสดงระดับความยากโดยรวม
    st.markdown(f"""
    <div class='overall-difficulty {difficulty_class}'>
        📊 ระดับความยากโดยรวม: {emoji} {overall_difficulty}
    </div>
    """, unsafe_allow_html=True)

    # แสดงรายละเอียดระดับความยาก
    st.markdown("""
    <div class='difficulty-summary'>
        <div class='difficulty-item difficulty-easy'>
            <h3>🟢 ง่าย</h3>
            <p style='font-size: 24px; font-weight: bold;'>{}</p>
            <p>{} ข้อ ({:.1f}%)</p>
        </div>
        <div class='difficulty-item difficulty-medium'>
            <h3>🟡 ปานกลาง</h3>
            <p style='font-size: 24px; font-weight: bold;'>{}</p>
            <p>{} ข้อ ({:.1f}%)</p>
        </div>
        <div class='difficulty-item difficulty-hard'>
            <h3>🔴 ยาก</h3>
            <p style='font-size: 24px; font-weight: bold;'>{}</p>
            <p>{} ข้อ ({:.1f}%)</p>
        </div>
    </div>
    """.format(
        easy_count, easy_count, easy_pct,
        medium_count, medium_count, medium_pct,
        hard_count, hard_count, hard_pct
    ), unsafe_allow_html=True)

def display_analysis_results(analysis_result, min_questions_req, min_choices_req):
    """แสดงผลการวิเคราะห์แบบสวยงาม"""
    result = analysis_result
    st.markdown(f"""
    <div class='result-box info'>
        <h3>📊 ผลการวิเคราะห์ข้อสอบ</h3>
        <p><strong>✅ จำนวนข้อสอบทั้งหมด:</strong> {result['total_questions']} ข้อ</p>
        <p><strong>✅ จำนวนตัวเลือกทั้งหมด:</strong> {result['total_choices']} ตัวเลือก</p>
        <p><strong>✅ จำนวนข้อที่มีตัวเลือก:</strong> {result['questions_with_choices']} ข้อ</p>
        <p><strong>📋 เกณฑ์มาตรฐาน:</strong> ข้อสอบ ≥ {min_questions_req}, ข้อมีตัวเลือก ≥ {min_choices_req}</p>
    </div>
    """, unsafe_allow_html=True)

    # แสดงการวิเคราะห์ระดับความยาก
    display_difficulty_analysis(analysis_result)

    # ตรวจสอบมาตรฐาน - ใช้ค่าที่ส่งเข้ามา
    passed = (result['total_questions'] >= min_questions_req and
              result['questions_with_choices'] >= min_choices_req)
    if passed:
        st.markdown("""
        <div class='result-box success'>
            <h3>🎉 ผ่านเกณฑ์มาตรฐาน!</h3>
            <p>ข้อสอบชุดนี้ได้มาตรฐานแล้ว ✅</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='result-box warning'>
            <h3>⚠️ ยังไม่ผ่านเกณฑ์มาตรฐาน</h3>
        </div>
        """, unsafe_allow_html=True)
        issues = []
        # ใช้ค่าที่ส่งเข้ามาเพื่อแสดงข้อความ
        if result['total_questions'] < min_questions_req:
            issues.append(f"ต้องเพิ่มข้อสอบอีก {min_questions_req - result['total_questions']} ข้อ")
        if result['questions_with_choices'] < min_choices_req:
            issues.append(f"ต้องเพิ่มข้อที่มีตัวเลือกอีก {min_choices_req - result['questions_with_choices']} ข้อ")

        for issue in issues:
            st.markdown(f"<p style='margin-left: 20px;'>• {issue}</p>", unsafe_allow_html=True)

def display_detailed_questions(questions):
    """แสดงรายละเอียดคำถามแต่ละข้อ พร้อมระดับความยาก เหตุผล และคำแนะนำ"""
    if questions:
        st.subheader("📋 รายละเอียดข้อสอบ")
        with st.expander("ดูรายละเอียดทั้งหมดพร้อมคำแนะนำ", expanded=False):
            for i, question in enumerate(questions[:30]):  # แสดง 30 ข้อแรก
                with st.container():
                    # กำหนดสัญลักษณ์ตามระดับความยาก
                    difficulty_emoji = {
                        'ง่าย': '🟢',
                        'ปานกลาง': '🟡',
                        'ยาก': '🔴'
                    }.get(question.get('difficulty', 'ไม่ทราบ'), '⚪')

                    st.markdown(f"**คำถามที่ {question['number']} {difficulty_emoji} [{question.get('difficulty', 'ไม่ทราบ')}]:** {question['text']}")

                    # แสดงระดับ Bloom's (ถ้ามี)
                    if 'bloom_level' in question and question['bloom_level']:
                        st.markdown(f"<div class='bloom-level'><b>🧠 วิเคราะห์ตาม Bloom's:</b> ระดับ {question['bloom_level']}</div>", unsafe_allow_html=True)
                        # แสดง indicators ที่พบ
                        if 'bloom_indicators' in question and isinstance(question['bloom_indicators'], list):
                             st.markdown(f"<small><i>🔍 พบคำ/รูปแบบ: {', '.join(question['bloom_indicators'][:3])}</i></small>", unsafe_allow_html=True)
                        elif 'bloom_indicators' in question and isinstance(question['bloom_indicators'], str):
                             # กรณี fallback
                             st.markdown(f"<small><i>🔍 เหตุผล (Fallback): {question['bloom_indicators']}</i></small>", unsafe_allow_html=True)

                    # คำแนะนำ (สามารถปรับปรุงเพิ่มเติมได้)
                    suggestions = []
                    if question.get('bloom_level') == "Remembering":
                        suggestions.append("คำถามระดับ Remembering เหมาะสำหรับทบทวนพื้นฐาน")
                    elif question.get('bloom_level') == "Understanding":
                        suggestions.append("คำถามระดับ Understanding ช่วยเสริมความเข้าใจ")
                    elif question.get('bloom_level') == "Applying":
                        suggestions.append("คำถามระดับ Applying ช่วยพัฒนาทักษะการนำไปใช้")
                    elif question.get('bloom_level') == "Analyzing":
                        suggestions.append("คำถามระดับ Analyzing ช่วยพัฒนาทักษะการวิเคราะห์")
                    elif question.get('bloom_level') == "Evaluating":
                        suggestions.append("คำถามระดับ Evaluating ช่วยพัฒนาทักษะการประเมิน")
                    elif question.get('bloom_level') == "Creating":
                        suggestions.append("คำถามระดับ Creating ช่วยพัฒนาทักษะการสร้างสรรค์")
                    elif question.get('bloom_level') == "ไม่พบ (Fallback)":
                        suggestions.append("ระบบใช้เกณฑ์รูปแบบคำถามในการวิเคราะห์")
                    
                    if suggestions:
                        suggestion_html = "<ul>"
                        for s in suggestions:
                            suggestion_html += f"<li>{s}</li>"
                        suggestion_html += "</ul>"
                        st.markdown(f"<div class='improvement-suggestion'><b>💡 คำแนะนำ:</b> {suggestion_html}</div>", unsafe_allow_html=True)

                    if question['choices']:
                        st.markdown("**ตัวเลือก:**")
                        for choice in question['choices']:
                            st.markdown(f"- {choice}")
                    else:
                        st.markdown("*ไม่พบตัวเลือก*")
                    st.divider()

            if len(questions) > 30:
                st.info(f"แสดงเฉพาะ 30 ข้อแรก จากทั้งหมด {len(questions)} ข้อ")

# 🔍 ตรวจสอบความพร้อมของระบบ
system_errors = validate_system_requirements()
if system_errors:
    st.error("❌ ระบบยังไม่พร้อมใช้งาน:")
    for error in system_errors:
        st.markdown(f"- {error}")
    st.info("กรุณาตรวจสอบการติดตั้ง Tesseract-OCR และ Poppler")

if st.button("🔍 ตรวจสอบมาตรฐานข้อสอบ", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.warning("กรุณาอัพโหลดไฟล์ PDF ก่อนนะครับ")
    else:
        # อ่านค่าเกณฑ์มาตรฐานจาก session_state
        current_min_questions = st.session_state.get('min_questions', 10)
        current_min_choices = st.session_state.get('min_choices', 5)

        with st.spinner("กำลังประมวลผลไฟล์ PDF..."):
            try:
                # อ่าน PDF
                pdf_bytes = uploaded_file.read()
                # Reset file pointer for PdfReader
                uploaded_file.seek(0)
                pdf_reader = PdfReader(uploaded_file)

                # ดึงข้อความจาก PDF
                st.info("📄 กำลังดึงข้อความจาก PDF...")
                text = extract_text_from_pdf(pdf_reader)

                # ถ้าไม่พบข้อความ ให้ใช้ OCR
                if not text.strip() and OCR_AVAILABLE:
                    st.warning("❗️ ไม่พบข้อความใน PDF → กำลังใช้ OCR อ่าน...")
                    # บันทึกไฟล์ชั่วคราวเพื่อใช้กับ OCR
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(pdf_bytes)
                        tmp_file_path = tmp_file.name

                    try:
                        text = ocr_pdf_pages(tmp_file_path)
                        if text.strip():
                            st.success("✅ อ่านข้อความด้วย OCR สำเร็จ")
                        else:
                            st.error("❌ OCR อ่านไม่ได้ (ไฟล์อาจเบลอหรือสแกนไม่ชัด)")
                    finally:
                        # ลบไฟล์ชั่วคราว
                        if os.path.exists(tmp_file_path):
                            os.unlink(tmp_file_path)
                elif not text.strip():
                    st.error("❌ ไม่สามารถดึงข้อความจาก PDF ได้ และระบบ OCR ไม่พร้อมใช้งาน")
                else:
                    st.success("✅ ดึงข้อความจาก PDF สำเร็จ")

                # วิเคราะห์ข้อสอบ
                if text.strip():
                    st.info("🧠 กำลังวิเคราะห์มาตรฐานข้อสอบและตาม Bloom's Taxonomy...")
                    analysis_result = analyze_exam_detailed(text)

                    # แสดงผลการวิเคราะห์ - ส่งค่าเกณฑ์มาตรฐานที่อ่านได้ไปด้วย
                    display_analysis_results(analysis_result, current_min_questions, current_min_choices)

                    # แสดงรายละเอียดคำถามพร้อมคำแนะนำ
                    display_detailed_questions(analysis_result['questions'])

                    # แสดงข้อความดิบที่ดึงได้ (สำหรับ debugging)
                    with st.expander("🔍 ดูข้อความดิบที่ดึงได้"):
                        st.text_area("Raw Text", text, height=200)

                else:
                    st.error("❌ ไม่สามารถดึงข้อความจากไฟล์ได้เลย กรุณาตรวจสอบไฟล์ PDF")

            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}")
                st.info("กรุณาตรวจสอบไฟล์ PDF ว่าไม่เสียหาย และลองใหม่อีกครั้ง")

# คำแนะนำการใช้งาน
st.sidebar.divider()
st.sidebar.subheader("ℹ️ คำแนะนำการใช้งาน")
st.sidebar.markdown("""
- อัพโหลดไฟล์ PDF ข้อสอบคณิตศาสตร์ ม.4
- ระบบจะตรวจทั้งจาก PDF และ OCR อัตโนมัติ
- ระบบจะวิเคราะห์:
  - จำนวนข้อสอบและตัวเลือก
  - ผ่านเกณฑ์มาตรฐานที่กำหนดหรือไม่
  - ระดับความยากตาม Bloom's Taxonomy
""")

# ข้อมูลเกี่ยวกับระบบ
st.sidebar.divider()
st.sidebar.subheader("🤖 เกี่ยวกับระบบ")
st.sidebar.markdown("""
**เทคโนโลยีที่ใช้:**
- Streamlit
- PyPDF2
- Tesseract OCR
- pdf2image

**รองรับ:**
- ไฟล์ PDF ปกติ
- ไฟล์ PDF สแกน
- ภาษาไทยและภาษาอังกฤษ
""")

# เพิ่มข้อมูลเกี่ยวกับ Bloom's Taxonomy
st.sidebar.divider()
st.sidebar.subheader("📈 Bloom's Taxonomy สำหรับคณิตศาสตร์")
st.sidebar.markdown("""
- **Remembering (จำ):** จำสูตร, นิยาม
- **Understanding (เข้าใจ):** อธิบาย, ตีความ
- **Applying (นำไปใช้):** คำนวณ, แก้สมการ
- **Analyzing (วิเคราะห์):** เปรียบเทียบ, ตรวจสอบ
- **Evaluating (ประเมิน):** พิสูจน์, ให้เหตุผล
- **Creating (สร้าง):** ออกแบบโจทย์, ประดิษฐ์
""")