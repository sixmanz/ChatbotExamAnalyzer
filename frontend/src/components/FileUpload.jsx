import React, { useState } from 'react';
import axios from 'axios';
import { Upload, X, FileText, Loader2, AlertCircle, Rocket, Zap, Settings, ChevronDown, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const PROVIDERS = {
    "วิเคราะห์มาตรฐาน (Gemini)": [
        "โหมดแนะนำ (Gemini 2.0)",
        "โหมดรวดเร็ว (Gemini 1.5)",
        "โหมดแม่นยำสูง (Gemini Pro)"
    ],
    "วิเคราะห์รวดเร็ว (Groq/Llama)": [
        "Llama 3.3 70B (แนะนำ)",
        "Llama 3.1 8B (เร็ว)",
        "Mixtral 8x7B"
    ],
    "⚔️ โหมดเปรียบเทียบผู้เชี่ยวชาญ": [
        "Gemini vs Llama 3"
    ]
};

const FileUpload = ({ onAnalysisComplete, onBack }) => {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle');
    const [error, setError] = useState(null);
    const [selectedProvider, setSelectedProvider] = useState("วิเคราะห์มาตรฐาน (Gemini)");
    const [selectedModel, setSelectedModel] = useState("โหมดแนะนำ (Gemini 2.0)");
    const [showSettings, setShowSettings] = useState(false);
    const [isDragging, setIsDragging] = useState(false);

    const handleFile = (selected) => {
        if (selected) {
            const ext = selected.name.split('.').pop().toLowerCase();
            if (['pdf', 'docx', 'txt'].includes(ext)) {
                setFile(selected);
                setError(null);
            } else {
                setError("กรุณาอัปโหลดไฟล์ PDF, DOCX, หรือ TXT เท่านั้น");
            }
        }
    };

    const uploadAndExtract = async () => {
        if (!file) return;
        setStatus('uploading');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await axios.post('http://localhost:8000/api/upload', formData);
            const { questions: extractedQs, filename } = response.data;
            if (extractedQs.length > 0) {
                startAnalysis(extractedQs, filename);
            } else {
                setStatus('error');
                setError("ไม่พบข้อความที่เป็นข้อสอบในไฟล์นี้");
            }
        } catch (err) {
            setStatus('error');
            setError("เกิดข้อผิดพลาดในการอัปโหลดไฟล์");
        }
    };

    const startAnalysis = async (qs, filename) => {
        setStatus('analyzing');
        try {
            const response = await axios.post('http://localhost:8000/api/analyze', {
                questions: qs,
                provider: selectedProvider,
                model: selectedModel,
                filename: filename
            });
            onAnalysisComplete(response.data, qs, filename);
        } catch (err) {
            setStatus('error');
            setError("การวิเคราะห์ขัดข้อง กรุณาลองใหม่");
        }
    };

    return (
        <div className="container mx-auto px-8 mt-12 max-w-2xl animate-fade">
            <AnimatePresence mode="wait">
                {status === 'idle' && (
                    <motion.div
                        key="idle"
                        initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}
                        className={`bg-white rounded-3xl p-10 text-center border-2 border-dashed transition-all ${isDragging ? 'border-primary bg-indigo-50/50 scale-[1.01]' : 'border-slate-200'}`}
                        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFile(e.dataTransfer.files[0]); }}
                    >
                        <div className="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
                            <Upload size={32} className="text-primary" />
                        </div>

                        {!file ? (
                            <>
                                <h3 className="text-2xl font-bold mb-3 text-slate-800 tracking-tight">ขั้นตอนที่ 1: อัปโหลดข้อสอบ</h3>
                                <p className="text-slate-500 mb-10 text-sm leading-relaxed max-w-sm mx-auto">
                                    ลากไฟล์ข้อสอบมาวาง (PDF, Word, หรือ TXT) <br />
                                    เพื่อให้ผู้ช่วย AI เริ่มต้นการวิเคราะห์คุณลักษณะรายข้อ
                                </p>
                                <input type="file" id="fileInput" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
                                <label htmlFor="fileInput" className="btn btn-primary px-10">เลือกไฟล์จากเครื่อง</label>
                            </>
                        ) : (
                            <div className="animate-fade">
                                <div className="flex items-center justify-between bg-slate-50 p-4 rounded-xl mb-8 border border-slate-100">
                                    <div className="flex items-center gap-3">
                                        <FileText size={20} className="text-primary" />
                                        <span className="font-semibold text-slate-700 truncate max-w-[250px]">{file.name}</span>
                                    </div>
                                    <button onClick={() => setFile(null)} className="p-1.5 hover:bg-slate-200 rounded-full transition-colors">
                                        <X size={18} className="text-slate-500" />
                                    </button>
                                </div>

                                <div className="mb-8">
                                    <button
                                        onClick={() => setShowSettings(!showSettings)}
                                        className="text-xs font-bold text-slate-400 uppercase tracking-widest hover:text-primary transition-colors flex items-center gap-2 mx-auto mb-2"
                                    >
                                        <Settings size={14} /> โหมดการวิเคราะห์ (ขั้นสูง)
                                    </button>
                                    <AnimatePresence>
                                        {showSettings && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                                                className="overflow-hidden bg-slate-50 rounded-xl p-6 border border-slate-100 text-left mb-6"
                                            >
                                                <div className="mb-4">
                                                    <label className="text-[10px] uppercase font-bold text-slate-400 mb-2 block">เลือกผู้เชี่ยวชาญ</label>
                                                    <select
                                                        className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-sm focus:border-primary focus:outline-none"
                                                        value={selectedProvider}
                                                        onChange={(e) => setSelectedProvider(e.target.value)}
                                                    >
                                                        {Object.keys(PROVIDERS).map(p => <option key={p} value={p}>{p}</option>)}
                                                    </select>
                                                </div>
                                                <div>
                                                    <label className="text-[10px] uppercase font-bold text-slate-400 mb-2 block">ระดับความละเอียด</label>
                                                    <select className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-sm focus:border-primary focus:outline-none">
                                                        {PROVIDERS[selectedProvider]?.map(m => <option key={m} value={m}>{m}</option>)}
                                                    </select>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>

                                <button className="btn btn-primary w-full py-4 text-lg" onClick={uploadAndExtract}>
                                    <Zap size={20} /> เริ่มการวิเคราะห์คุณภาพข้อสอบ
                                </button>
                            </div>
                        )}

                        <button onClick={onBack} className="mt-8 text-sm font-semibold text-slate-400 hover:text-primary transition-colors">
                            กลับหน้าหลัก
                        </button>
                    </motion.div>
                )}

                {status.includes('ing') && (
                    <motion.div
                        key="loading"
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="bg-white rounded-3xl p-20 text-center border border-slate-100 shadow-sm"
                    >
                        <div className="relative w-24 h-24 mx-auto mb-8 flex items-center justify-center">
                            <motion.div
                                className="absolute inset-0 border-4 border-slate-100 border-t-primary rounded-full"
                                animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                            />
                            <Check size={32} className="text-primary animate-pulse" />
                        </div>
                        <h3 className="text-2xl font-bold text-slate-800 mb-2">
                            {status === 'uploading' ? 'กำลังอ่านข้อสอบ...' : 'ผู้ช่วย AI กำลังวิเคราะห์...'}
                        </h3>
                        <p className="text-slate-500 text-sm">กรุณารอสักครู่ เครื่องมือกำลังตรวจสอบคุณภาพรายข้อตามหลักวิชาการ</p>
                    </motion.div>
                )}

                {status === 'error' && (
                    <motion.div
                        key="error"
                        className="bg-white rounded-3xl p-16 text-center border border-error/10 shadow-sm"
                    >
                        <AlertCircle size={48} className="text-error mx-auto mb-6" />
                        <h3 className="text-2xl font-bold text-slate-800 mb-2">ไม่สามารถดำเนินการต่อได้</h3>
                        <p className="text-slate-500 mb-8">{error}</p>
                        <button className="btn transition-all bg-slate-100 hover:bg-slate-200 text-slate-700" onClick={() => setStatus('idle')}>ลองใหม่อีกครั้ง</button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default FileUpload;
