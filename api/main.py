import io
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Internal Imports
from src.utils import (
    extract_text_from_pdf, 
    extract_text_from_docx, 
    export_to_excel, 
    export_to_word,
    save_analysis_history
)
from src.analysis import (
    extract_questions, 
    analyze_question,
    improve_question_with_ai,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL_NAME
)
from src.database import (
    add_to_question_bank, 
    get_recent_exams, 
    load_exam_results,
    delete_exam,
    clear_all_history
)

app = FastAPI(title="AI Exam Analyzer API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class AnalysisRequest(BaseModel):
    questions: List[str]
    provider: Optional[str] = DEFAULT_PROVIDER
    model: Optional[str] = DEFAULT_MODEL_NAME
    filename: Optional[str] = "Untitled_Exam"
    subject: Optional[str] = "ทั่วไป"
    grade_level: Optional[str] = "ไม่ระบุ"

class FixRequest(BaseModel):
    question_text: str
    suggestion: str
    provider: Optional[str] = DEFAULT_PROVIDER

class SaveRequest(BaseModel):
    question_text: str
    analysis: dict
    subject: Optional[str] = ""
    filename: Optional[str] = ""

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "AI Exam Analyzer API is running"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and extract questions"""
    try:
        content = await file.read()
        file_like = io.BytesIO(content)
        
        text = ""
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext == ".pdf":
            text = extract_text_from_pdf(file_like)
        elif file_ext == ".docx":
            text = extract_text_from_docx(file_like)
        elif file_ext == ".txt":
            text = content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
            
        questions = extract_questions(text)
        
        return {
            "filename": file.filename,
            "questions": questions,
            "count": len(questions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_questions_endpoint(request: AnalysisRequest):
    """Analyze a list of questions"""
    results = []
    for i, q_text in enumerate(request.questions):
        analysis = analyze_question(
            q_text, 
            i + 1, 
            provider=request.provider,
            model_name=request.model,
            subject=request.subject,
            grade_level=request.grade_level
        )
        analysis['question_text'] = q_text # Store original text for history persistence
        results.append(analysis)
    
    # Save to history automatically
    if results:
        summary = f"Analyzed {len(results)} questions via {request.provider}"
        save_analysis_history(request.filename, results, summary)
        
    return results

@app.get("/api/history")
async def get_history():
    """Fetch recent exam analysis history"""
    return get_recent_exams()

@app.delete("/api/history/{exam_id}")
async def delete_history_item(exam_id: int):
    """Delete a specific history record"""
    delete_exam(exam_id)
    return {"status": "success"}

@app.delete("/api/history")
async def delete_all_history():
    """Clear all history"""
    clear_all_history()
    return {"status": "success"}

@app.post("/api/fix")
async def fix_question(request: FixRequest):
    """Get AI improvement for a question"""
    new_q, err = improve_question_with_ai(request.question_text, request.suggestion, request.provider)
    if err:
        raise HTTPException(status_code=500, detail=err)
    return {"improved_text": new_q}

@app.post("/api/save")
async def save_to_bank(request: SaveRequest):
    """Save a question to the question bank"""
    try:
        add_to_question_bank(request.question_text, request.analysis, request.subject, request.filename)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/excel")
async def export_excel(results: List[dict]):
    """Export results as Excel"""
    output = export_to_excel(results)
    if not output:
        raise HTTPException(status_code=500, detail="Excel export failed")
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=exam_analysis.xlsx"}
    )

@app.post("/api/export/word")
async def export_word(results: List[dict]):
    """Export results as Word"""
    output = export_to_word(results)
    if not output:
        raise HTTPException(status_code=500, detail="Word export failed")
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=exam_analysis.docx"}
    )
