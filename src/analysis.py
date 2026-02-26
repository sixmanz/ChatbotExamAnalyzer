# -*- coding: utf-8 -*-
import os
import re
import json
import time # Fixed missing import
import google.generativeai as genai
from google.generativeai.types import GenerationConfig 
from dotenv import load_dotenv

# Internal Imports
from .utils import load_prompts, clean_and_normalize, sanitize_analysis, create_error_response

# Load Env
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '').strip()

# Configuration
AI_PROVIDERS = {
    "Gemini (Google)": {
        "models": {
            "Gemini 2.0 Flash (แนะนำ)": "gemini-2.0-flash",
            "Gemini 1.5 Flash (เร็ว)": "gemini-1.5-flash-latest",
            "Gemini 1.5 Pro (แม่นยำ)": "gemini-1.5-pro-latest",
        },
        "api_key": GEMINI_API_KEY,
    },
    "Groq (ฟรี+เร็วมาก)": {
        "models": {
            "Llama 3.3 70B (แนะนำ)": "llama-3.3-70b-versatile",
            "Llama 3.1 8B (เร็ว)": "llama-3.1-8b-instant",
            "Mixtral 8x7B": "mixtral-8x7b-32768",
        },
        "api_key": GROQ_API_KEY,
    },
    "OpenRouter (หลายโมเดลฟรี)": {
        "models": {
            "Llama 3.2 3B (ฟรี)": "meta-llama/llama-3.2-3b-instruct:free",
            "Mistral 7B (ฟรี)": "mistralai/mistral-7b-instruct:free",
            "Gemma 2 9B (ฟรี)": "google/gemma-2-9b-it:free",
        },
        "api_key": OPENROUTER_API_KEY,
    },
    "⚔️ Battle Mode (Gemini vs Groq)": {
        "models": {
            "Default (Gemini Flash vs Llama 3)": "battle-mode"
        },
        "api_key": "BOTH"
    }
}

DEFAULT_PROVIDER = "Gemini (Google)"
DEFAULT_MODEL_NAME = "Gemini 2.0 Flash (แนะนำ)"

# Constants
GEMINI_AVAILABLE = len(GEMINI_API_KEY) > 30
GROQ_AVAILABLE = len(GROQ_API_KEY) > 20
OPENROUTER_AVAILABLE = len(OPENROUTER_API_KEY) > 20
AVAILABLE_AI_MODELS = AI_PROVIDERS[DEFAULT_PROVIDER]["models"] # Legacy compat

SYSTEM_INSTRUCTION_PROMPT, FEW_SHOT_PROMPT_TEMPLATE = load_prompts()

# --- Extraction Logic ---
def extract_questions_with_ai(raw_text):
    """Fallback: ให้ AI ช่วยแยกข้อสอบเมื่อ Regex เอาไม่อยู่"""
    if not GEMINI_AVAILABLE:
        return []

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash-latest") 
        
        prompt = f"""
        You are an expert exam parser. 
        Please extract all exam questions from the following text and return them as a JSON list of strings.
        
        Rules:
        1. Capture the full question text including the question number and all options (e.g. "1. Question... A. Opt...").
        2. Do not change the original text, just split it correctly.
        3. If there are no clear questions, return an empty list.
        4. Return ONLY raw JSON Array.

        Text to parse:
        {raw_text[:20000]} 
        """
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        questions = json.loads(response.text)
        
        if isinstance(questions, list):
            return [str(q).strip() for q in questions]
        else:
            return []
            
    except Exception as e:
        print(f"AI Extraction Failed: {e}")
        return []

# --- Extraction Logic ---
def extract_questions(raw_text):
    """สกัดข้อสอบเป็นรายข้อ (ปรับปรุงให้รองรับหลายรูปแบบ: 1., 1), (1), ข้อ 1, ข้อที่ 1)"""
    # 1. ทำความสะอาดข้อความทั้งหมด
    text = re.split(r"={10,}\s*เฉลย\s*={10,}", raw_text, flags=re.DOTALL | re.IGNORECASE)[0]
    cleaned_text = clean_and_normalize(text)
    
    # 2. Regex สำหรับจับเลขข้อ (Capturing Group for Split)
    # จับ: 1. / 1) / (1) / ข้อ 1 / ข้อที่ 1
    # Note: Wrap in (...) to keep the delimiter in split results
    question_pattern = r'((?:^|\n)\s*(?:ข้อ(?:ที่)?\s*)?\d+(?:[\.\)]|(?<=\()\d+\)))'
    chunks = re.split(question_pattern, cleaned_text)
    
    questions = []
    
    # Skip preamble
    start_idx = 0
    if len(chunks) > 0 and not chunks[0].strip():
        start_idx = 1
    elif len(chunks) > 0 and not re.match(r'(?:ข้อ\s*\d+|ข้อที่\s*\d+|\d+\.|(?:\(?\d+\)))', chunks[0].strip()):
        start_idx = 1 

    for i in range(start_idx, len(chunks), 2):
        if i+1 < len(chunks):
            delim = chunks[i]
            content = chunks[i+1]
            full_q = delim + content
            questions.append(full_q.strip())

    # 3. Validation
    valid_questions = []
    extracted_indices = []

    for q in questions:
        q = q.strip()
        if len(q) < 5: continue 
        
        match_idx = re.match(r'^(\d+)', q)
        if match_idx:
            extracted_indices.append(int(match_idx.group(1)))

        has_std_options = len(re.findall(r'[ก-งA-D]\.', q)) >= 2
        
        if has_std_options:
            q_formatted = re.sub(r'(\s+)([ก-งA-D]\.)', r'\n\2', q)
            valid_questions.append(q_formatted)
        else:
            if len(q) > 10: 
                valid_questions.append(q)
    


    # --- 4. AI Fallback (Robustness for Complex Formats) ---
    # If Regex found too few questions (< 2) but text is long (> 300 chars), try AI.
    if len(valid_questions) < 2 and len(raw_text) > 300:
        if GEMINI_AVAILABLE:
            ai_questions = extract_questions_with_ai(cleaned_text)
            if len(ai_questions) > len(valid_questions):
                return ai_questions

    return valid_questions

# --- Analysis Logic ---
def build_analysis_prompt(question_text, question_id=1, custom_prompt="", language='th', subject="ทั่วไป", grade_level="ไม่ระบุ"):
    """สร้าง Prompt ที่เป็นมาตรฐานเดียวกันทุก Provider โดยระบุวิชาและระดับชั้น"""
    
    # Subject context
    context_instruction = f"\n[บริบท: วิชา {subject}, ระดับชั้น {grade_level}]"
    
    # Language Instruction
    lang_instruction = "IMPORTANT: Please output your analysis reasoning inside the JSON in Thai language."
    if language == 'en':
         lang_instruction = "IMPORTANT: Please output your analysis reasoning inside the JSON in English language."

    # --- RAG Injection (Define Before Use) ---
    rag_context = ""
    try:
        from .rag import rag_engine
        if rag_engine.curriculum_text:
            relevant_std = rag_engine.search(question_text)
            rag_context = f"\n\n**REFERENCE CURRICULUM:**\n{relevant_std}\n(Use this reference to determine 'curriculum_standard')"
    except ImportError:
        pass # Handle RAG module missing cleanly

    if custom_prompt:
         # --- PURE CUSTOM PROMPT MODE ---
         # User wants full control. We minimal interference.
         system_prompt = custom_prompt
         # Safety: Ensure JSON format is mentioned if user forgot (to prevent crash)
         if "json" not in custom_prompt.lower():
             system_prompt += "\n\n(IMPORTANT: Please return response in raw JSON format to ensure compatibility)"
         
         # User Message: Just the question context
         user_message = f"""Question {question_id}:
{question_text}
{rag_context}"""

    else:
         # --- DEFAULT MODE (Strict Schema) ---
         system_prompt = SYSTEM_INSTRUCTION_PROMPT + f"\n\n{lang_instruction}"
         
         if language == 'en':
            valid_difficulty = "Easy, Medium, Hard"
            valid_options = "A, B, C, D"
            user_message = f"""Question {question_id}:
{question_text}
{rag_context}

Analyze and answer in JSON only (No Markdown text). Required keys: 
- bloom_level (String: Remember, Understand, Apply, Analyze, Evaluate, Create)
- reasoning (String)
- difficulty (String: {valid_difficulty})
- curriculum_standard (String: cite the code from Reference Curriculum if matched)
- correct_option (String: {valid_options})
- correct_option_analysis (String)
- distractor_analysis (String)
- why_good_distractor (String)
- is_good_question (Boolean)
- improvement_suggestion (String)"""

         else:
            valid_difficulty = "ง่าย, ปานกลาง, ยาก"
            valid_options = "ก, ข, ค, ง"
            user_message = f"""{context_instruction}
คำถามข้อที่ {question_id}:
{question_text}
{rag_context}

วิเคราะห์และตอบเป็น JSON เท่านั้น (ไม่ต้องมี Markdown text) โดยมี keys: 
- bloom_level (String: Remember, Understand, Apply, Analyze, Evaluate, Create)
- reasoning (String)
- difficulty (String: {valid_difficulty})
- curriculum_standard (String: ระบุรหัสตัวชี้วัดจาก Reference Curriculum ถ้าตรง)
- correct_option (String: {valid_options})
- correct_option_analysis (String)
- distractor_analysis (String)
- why_good_distractor (String)
- is_good_question (Boolean)
- improvement_suggestion (String)"""

    return system_prompt, user_message

def analyze_with_gemini(question_text, question_id=1, provider_config=None, model_name=DEFAULT_MODEL_NAME, custom_prompt="", language='th', subject="ทั่วไป", grade_level="ไม่ระบุ"):
    """เรียกใช้ Gemini API เพื่อวิเคราะห์ข้อสอบ"""
    if not GEMINI_AVAILABLE:
        return create_error_response("ไม่พบ GEMINI_API_KEY")

    system_instruction, user_message = build_analysis_prompt(question_text, question_id, custom_prompt, language, subject, grade_level)

    model_id = AVAILABLE_AI_MODELS.get(model_name, "gemini-2.0-flash")

    # Re-configure to ensure key is set
    genai.configure(api_key=GEMINI_API_KEY)
    
    model = genai.GenerativeModel(
        model_id, 
        system_instruction=system_instruction
    )
    
    GEMINI_SCHEMA = {
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

    config = GenerationConfig( 
        response_mime_type="application/json", 
        max_output_tokens=2048,
        temperature=0.2,
        response_schema=GEMINI_SCHEMA
    )
    
    last_error_message = ""
    max_retries = 3  # Reduced from 5 for faster failure

    for attempt in range(max_retries):
        if attempt > 0:
            # Optimized: faster retry (2-6 seconds max instead of 60)
            base_delay = min(6, (2 ** attempt))
            time.sleep(base_delay)
            
        try:
            response = model.generate_content(
                user_message, 
                generation_config=config, 
            )
            raw_text = response.text.strip()
        
            cleaned_json = re.sub(r'^```(?:json)?\s*|```$', '', raw_text, flags=re.MULTILINE | re.DOTALL).strip()
            start_brace = cleaned_json.find('{')
            end_brace = cleaned_json.rfind('}')
            
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                cleaned_json = cleaned_json[start_brace:end_brace+1].strip()
            else:
                raise ValueError("Could not find valid JSON structure.") 
            
            analysis = json.loads(cleaned_json)
            return sanitize_analysis(analysis)

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_error_message = f"ข้อผิดพลาดในการประมวลผล JSON: {type(e).__name__}"
            if attempt < max_retries - 1: continue
            
        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = any([x in error_str for x in ["429", "quota", "resourceexhausted", "too many requests"]])
            
            if is_rate_limit:
                if attempt < max_retries - 1:
                    # Optimized: max 30s instead of 120s
                    retry_delay = min(30, 10 * (attempt + 1))
                    time.sleep(retry_delay)
                    continue
                else:
                    return create_error_response("Quota Exceeded (Rate Limit)")
            else:
                last_error_message = f"ข้อผิดพลาด: {str(e)}"
                if attempt < max_retries - 1: continue

    return create_error_response(last_error_message)

def analyze_with_groq(question_text, question_id=1, model_name="Llama 3.3 70B (แนะนำ)", subject="ทั่วไป", grade_level="ไม่ระบุ"):
    """วิเคราะห์ข้อสอบผ่าน Groq API"""
    if not GROQ_AVAILABLE:
        return create_error_response("ไม่พบ GROQ_API_KEY")
    
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    
    model_id = AI_PROVIDERS["Groq (ฟรี+เร็วมาก)"]["models"].get(model_name, "llama-3.3-70b-versatile")
    
    system_prompt, user_message = build_analysis_prompt(question_text, question_id, subject=subject, grade_level=grade_level)
    
    max_retries = 3
    last_error = ""
    
    for attempt in range(max_retries):
        if attempt > 0: time.sleep(attempt * 2)
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content
            analysis = json.loads(raw_text)
            return sanitize_analysis(analysis)
        except Exception as e:
            last_error = str(e)
            if "429" in last_error: time.sleep(5)
            
    return create_error_response(f"Groq Error: {last_error}")

def analyze_with_openrouter(question_text, question_id=1, model_name="Llama 3.2 3B (ฟรี)", subject="ทั่วไป", grade_level="ไม่ระบุ"):
    """วิเคราะห์ข้อสอบผ่าน OpenRouter API"""
    if not OPENROUTER_AVAILABLE:
        return create_error_response("ไม่พบ OPENROUTER_API_KEY")
    
    import openai
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )
    
    model_id = AI_PROVIDERS["OpenRouter (หลายโมเดลฟรี)"]["models"].get(model_name, "meta-llama/llama-3.2-3b-instruct:free")
    
    system_prompt, user_message = build_analysis_prompt(question_text, question_id, subject=subject, grade_level=grade_level)
    
    max_retries = 3
    last_error = ""
    
    for attempt in range(max_retries):
        if attempt > 0: time.sleep(attempt * 2)
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            raw_text = response.choices[0].message.content
            cleaned = re.sub(r'^```(?:json)?\s*|```$', '', raw_text, flags=re.MULTILINE | re.DOTALL).strip()
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end > start: cleaned = cleaned[start:end+1]
            analysis = json.loads(cleaned)
            return sanitize_analysis(analysis)
        except Exception as e:
            last_error = str(e)
            if "429" in last_error: time.sleep(5)

    return create_error_response(f"OpenRouter Error: {last_error}")

def analyze_question(question_text, question_id=1, provider=DEFAULT_PROVIDER, model_name=DEFAULT_MODEL_NAME, subject="ทั่วไป", grade_level="ไม่ระบุ"):
    """Wrapper function"""
    if provider == "⚔️ Battle Mode (Gemini vs Groq)":
        return analyze_with_battle(question_text, question_id, subject=subject, grade_level=grade_level)
    elif provider == "Gemini (Google)":
        return analyze_with_gemini(question_text, question_id, model_name=model_name, subject=subject, grade_level=grade_level)
    elif provider == "Groq (ฟรี+เร็วมาก)":
        return analyze_with_groq(question_text, question_id, model_name=model_name, subject=subject, grade_level=grade_level)
    elif provider == "OpenRouter (หลายโมเดลฟรี)":
        return analyze_with_openrouter(question_text, question_id, model_name=model_name, subject=subject, grade_level=grade_level)
    else:
        return analyze_with_gemini(question_text, question_id, model_name=model_name, subject=subject, grade_level=grade_level)

def analyze_with_battle(question_text, question_id=1, subject="ทั่วไป", grade_level="ไม่ระบุ"):
    """เปรียบเทียบผลลัพธ์จาก 2 โมเดล (Gemini vs Groq)"""
    # 1. Analyze with Gemini
    res_gemini = analyze_with_gemini(question_text, question_id, subject=subject, grade_level=grade_level)
    
    # 2. Analyze with Groq (Llama 3)
    # Force use of default Groq model even if not selected
    res_groq = analyze_with_groq(question_text, question_id, subject=subject, grade_level=grade_level)
    
    # 3. Create a merged/comparison result
    # We will return Gemini's result as structure but append Battle Info
    
    battle_result = res_gemini.copy()
    battle_result["battle_info"] = {
        "model_a": "Gemini 2.0 Flash",
        "result_a": res_gemini,
        "model_b": "Llama 3.3 70B (Groq)",
        "result_b": res_groq
    }
    battle_result["improvement_suggestion"] = f"**Gemini:** {res_gemini.get('improvement_suggestion')}\n\n---\n\n**Llama 3:** {res_groq.get('improvement_suggestion')}"
    
    return battle_result

# --- Generation Logic ---
def generate_exam_with_ai(subject, num_questions=5, bloom_level="Apply", difficulty="ปานกลาง", provider=DEFAULT_PROVIDER):
    """สร้างชุดข้อสอบใหม่จาก AI"""
    prompt = f"""สร้างข้อสอบปรนัย 4 ตัวเลือก จำนวน {num_questions} ข้อ
วิชา: {subject}
Level: {bloom_level}
ระดับความยาก: {difficulty}

สำหรับแต่ละข้อ ให้มี:
1. คำถามที่ชัดเจน
2. ตัวเลือก ก. ข. ค. ง.
3. เฉลย
4. คำอธิบายคำตอบ

ตอบเป็น JSON array ที่มี keys: question, options (array), answer, explanation"""
    
    try:
        raw_text = ""
        if provider == "Gemini (Google)" and GEMINI_AVAILABLE:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            raw_text = response.text
        elif provider == "Groq (ฟรี+เร็วมาก)" and GROQ_AVAILABLE:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            raw_text = response.choices[0].message.content
        elif provider == "OpenRouter (หลายโมเดลฟรี)" and OPENROUTER_AVAILABLE:
            import openai
            client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
            response = client.chat.completions.create(
                model="meta-llama/llama-3.2-3b-instruct:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            raw_text = response.choices[0].message.content
        else:
            return None, "ไม่มี API Key ที่พร้อมใช้งาน"
        
        cleaned = re.sub(r'^```(?:json)?\s*|```$', '', raw_text, flags=re.MULTILINE | re.DOTALL).strip()
        start = cleaned.find('[')
        end = cleaned.rfind(']') + 1
        if start != -1 and end > start:
            exams = json.loads(cleaned[start:end])
            return exams, None
        return None, "ไม่สามารถ parse JSON ได้"
    except Exception as e:
        return None, str(e)

def improve_question_with_ai(question_text, suggestion, provider=DEFAULT_PROVIDER):
    """ปรับปรุงข้อสอบตามคำแนะนำ AI"""
    
    prompt = f"""ข้อสอบเดิม:
{question_text}

ข้อเสนอแนะในการปรับปรุง:
{suggestion}

กรุณาเขียนข้อสอบใหม่ที่ปรับปรุงตามข้อเสนอแนะ โดยยังคงเนื้อหาหลักไว้ แต่แก้ไขจุดบกพร่อง
ตอบเฉพาะข้อสอบที่ปรับปรุงแล้วเท่านั้น ในรูปแบบ:
- คำถาม
- ตัวเลือก ก. ข. ค. ง.
- (เฉลย: ตัวเลือกที่ถูกต้อง)"""
    
    try:
        if provider == "Gemini (Google)" and GEMINI_AVAILABLE:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text, None
        elif provider == "Groq (ฟรี+เร็วมาก)" and GROQ_AVAILABLE:
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            return response.choices[0].message.content, None
        elif provider == "OpenRouter (หลายโมเดลฟรี)" and OPENROUTER_AVAILABLE:
            import openai
            client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
            response = client.chat.completions.create(
                model="meta-llama/llama-3.2-3b-instruct:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            return response.choices[0].message.content, None
        return None, "ไม่มี API Key ที่พร้อมใช้งาน"
    except Exception as e:
        return None, str(e)
