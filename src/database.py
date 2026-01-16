# -*- coding: utf-8 -*-
import sqlite3
import json
import os
from datetime import datetime

DB_Name = "exams.db"

def init_db():
    """สร้างตารางใน Database ถ้ายังไม่มี"""
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        
        # Table: Exams (เก็บข้อมูลรวมของชุดข้อสอบ)
        c.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                timestamp TEXT,
                total_questions INTEGER,
                good_questions INTEGER,
                summary TEXT,
                raw_results TEXT  -- เก็บ JSON ผลลัพธ์ทั้งหมดไว้ในนี้
            )
        ''')
        conn.commit()

def save_exam_result(filename, results, summary):
    """บันทึกผลการวิเคราะห์ลง Database"""
    init_db() # Ensure DB exists
    
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        total = len(results)
        good = sum(1 for r in results if r.get('is_good_question'))
        raw_json = json.dumps(results, ensure_ascii=False)
        
        c.execute('''
            INSERT INTO exams (filename, timestamp, total_questions, good_questions, summary, raw_results)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, timestamp, total, good, summary, raw_json))
        conn.commit()

def get_recent_exams(limit=20):
    """ดึงประวัติล่าสุด"""
    init_db()
    with sqlite3.connect(DB_Name) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM exams ORDER BY id DESC LIMIT ?', (limit,))
        rows = c.fetchall()
        
        exams = []
        for row in rows:
            exams.append(dict(row))
        return exams

def load_exam_results(exam_id):
    """ดึงผลลัพธ์ของสอบ ID นั้นๆ"""
    init_db()  # Ensure DB exists
    with sqlite3.connect(DB_Name) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT raw_results FROM exams WHERE id = ?', (exam_id,))
        row = c.fetchone()
        
        if row:
            return json.loads(row['raw_results'])
        return None

def clear_all_history():
    """ลบประวัติทั้งหมด"""
    init_db()  # Ensure DB exists
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM exams')
        conn.commit()

# =====================================================
# QUESTION BANK - Save Good Questions for Reuse
# =====================================================

def init_question_bank():
    """สร้างตาราง Question Bank"""
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT,
                bloom_level TEXT,
                difficulty TEXT,
                subject TEXT,
                curriculum_standard TEXT,
                correct_option TEXT,
                added_at TEXT,
                source_filename TEXT
            )
        ''')
        conn.commit()

def add_to_question_bank(question_text, analysis, subject="", source_filename=""):
    """เพิ่มข้อสอบเข้า Bank"""
    init_question_bank()
    
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO question_bank 
            (question_text, bloom_level, difficulty, subject, curriculum_standard, correct_option, added_at, source_filename)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            question_text,
            analysis.get('bloom_level', ''),
            analysis.get('difficulty', ''),
            subject,
            analysis.get('curriculum_standard', ''),
            analysis.get('correct_option', ''),
            datetime.now().isoformat(),
            source_filename
        ))
        conn.commit()

def get_question_bank(subject_filter=None, bloom_filter=None, limit=100):
    """ดึงข้อสอบจาก Bank"""
    init_question_bank()
    
    with sqlite3.connect(DB_Name) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = 'SELECT * FROM question_bank WHERE 1=1'
        params = []
        
        if subject_filter:
            query += ' AND subject LIKE ?'
            params.append(f'%{subject_filter}%')
        if bloom_filter:
            query += ' AND bloom_level LIKE ?'
            params.append(f'%{bloom_filter}%')
            
        query += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        
        questions = [dict(row) for row in rows]
        return questions

def delete_from_question_bank(question_id):
    """ลบข้อสอบออกจาก Bank"""
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM question_bank WHERE id = ?', (question_id,))
        conn.commit()

def get_question_bank_stats():
    """สถิติ Question Bank"""
    init_question_bank()
    
    with sqlite3.connect(DB_Name) as conn:
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM question_bank')
        total_q = c.fetchone()
        total = total_q[0] if total_q else 0
        
        c.execute('SELECT bloom_level, COUNT(*) as cnt FROM question_bank GROUP BY bloom_level')
        by_bloom = {row[0]: row[1] for row in c.fetchall()}
        
        c.execute('SELECT subject, COUNT(*) as cnt FROM question_bank GROUP BY subject')
        by_subject = {row[0]: row[1] for row in c.fetchall()}
        
        return {"total": total, "by_bloom": by_bloom, "by_subject": by_subject}
