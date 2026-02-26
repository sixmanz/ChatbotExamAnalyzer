import React, { useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import {
    CheckCircle, AlertTriangle, ChevronDown, ChevronUp,
    FileSpreadsheet, FileText, Bookmark, Sparkles, Loader2,
    Swords, ArrowLeft, PlusCircle, LayoutDashboard, Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const BLOOM_TH = {
    "Remember": "ความจำ",
    "Understand": "ความเข้าใจ",
    "Apply": "การประยุกต์ใช้",
    "Analyze": "การวิเคราะห์",
    "Evaluate": "การประเมินค่า",
    "Create": "การสร้างสรรค์"
};

const BLOOM_COLORS = {
    "Remember": "#94a3b8",
    "Understand": "#38bdf8",
    "Apply": "#4f46e5",
    "Analyze": "#8b5cf6",
    "Evaluate": "#0ea5e9",
    "Create": "#ec4899"
};

const QuestionCard = ({ question, index, originalText, filename }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [fixedText, setFixedText] = useState(null);
    const [isFixing, setIsFixing] = useState(false);
    const [saveStatus, setSaveStatus] = useState('idle');
    const [battleView, setBattleView] = useState('model_a');

    const handleFix = async (e) => {
        e.stopPropagation();
        setIsFixing(true);
        try {
            const response = await axios.post('http://localhost:8000/api/fix', {
                question_text: originalText,
                suggestion: question.improvement_suggestion
            });
            setFixedText(response.data.improved_text);
        } catch (err) {
            alert("ไม่สามารถปรับปรุงข้อสอบได้");
        } finally {
            setIsFixing(false);
        }
    };

    const handleSave = async (e) => {
        e.stopPropagation();
        setSaveStatus('saving');
        try {
            await axios.post('http://localhost:8000/api/save', {
                question_text: originalText,
                analysis: question,
                filename: filename
            });
            setSaveStatus('saved');
        } catch (err) {
            alert("ไม่สามารถบันทึกข้อสอบได้");
            setSaveStatus('idle');
        }
    };

    const currentAnalysis = question.battle_info ? question.battle_info[battleView === 'model_a' ? 'result_a' : 'result_b'] : question;

    return (
        <div className="bg-white rounded-2xl mb-4 border border-slate-100 shadow-sm overflow-hidden transition-all hover:border-indigo-100">
            <div
                className="p-5 cursor-pointer flex items-center justify-between gap-4 group"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-4">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-xs shrink-0">
                        {index + 1}
                    </div>
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-600 text-white uppercase">
                                {BLOOM_TH[currentAnalysis.bloom_level] || currentAnalysis.bloom_level}
                            </span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-500 uppercase">
                                {currentAnalysis.difficulty}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {currentAnalysis.is_good_question ? (
                        <span className="text-[10px] font-bold text-success bg-green-50 px-2 py-1 rounded-full flex items-center gap-1">
                            <CheckCircle size={10} /> คุณภาพดี
                        </span>
                    ) : (
                        <span className="text-[10px] font-bold text-warning bg-yellow-50 px-2 py-1 rounded-full flex items-center gap-1">
                            <AlertTriangle size={10} /> ควรปรับปรุง
                        </span>
                    )}
                    {isExpanded ? <ChevronUp size={18} className="text-slate-300" /> : <ChevronDown size={18} className="text-slate-300 group-hover:text-indigo-600" />}
                </div>
            </div>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
                        className="overflow-hidden bg-slate-50/50 border-t border-slate-50"
                    >
                        <div className="p-8">
                            {question.battle_info && (
                                <div className="flex gap-2 mb-6 bg-white p-1 rounded-xl border border-slate-100 w-fit">
                                    <button
                                        className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${battleView === 'model_a' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-indigo-600'}`}
                                        onClick={(e) => { e.stopPropagation(); setBattleView('model_a'); }}
                                    >
                                        ผู้เชี่ยวชาญ A
                                    </button>
                                    <button
                                        className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${battleView === 'model_b' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-indigo-600'}`}
                                        onClick={(e) => { e.stopPropagation(); setBattleView('model_b'); }}
                                    >
                                        ผู้เชี่ยวชาญ B
                                    </button>
                                </div>
                            )}

                            <div className="grid grid-cols-1 lg:grid-cols-5 gap-10">
                                <div className="lg:col-span-3">
                                    <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-400 mb-4">
                                        <FileText size={14} /> เนื้อหาข้อสอบเดิม
                                    </h4>
                                    <div className="bg-white p-6 rounded-2xl border border-slate-100 text-slate-700 text-sm whitespace-pre-wrap leading-relaxed shadow-sm">
                                        {originalText}
                                    </div>

                                    {fixedText && (
                                        <div className="mt-8 animate-fade">
                                            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-green-600 mb-4">
                                                <Sparkles size={14} /> ข้อสอบที่ปรับปรุงแล้ว
                                            </h4>
                                            <div className="bg-green-50/40 p-6 rounded-2xl border border-green-100 text-slate-800 text-sm whitespace-pre-wrap leading-relaxed">
                                                {fixedText}
                                            </div>
                                        </div>
                                    )}

                                    <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-indigo-600 mt-8 mb-4">
                                        <Info size={14} /> เหตุผลและการวิเคราะห์
                                    </h4>
                                    <p className="text-sm text-slate-600 leading-relaxed italic border-l-4 border-indigo-100 pl-4">{currentAnalysis.reasoning}</p>
                                </div>

                                <div className="lg:col-span-2 space-y-4">
                                    <div className={`p-6 rounded-2xl border ${currentAnalysis.is_good_question ? 'bg-green-50 border-green-100' : 'bg-yellow-50 border-yellow-100'}`}>
                                        <h5 className={`font-bold text-xs mb-3 ${currentAnalysis.is_good_question ? 'text-green-700' : 'text-yellow-700'}`}>
                                            {currentAnalysis.is_good_question ? '✅ ผ่านเกณฑ์มาตรฐาน' : '⚠️ ข้อเสนอแนะการปรับปรุง'}
                                        </h5>
                                        <p className="text-xs text-slate-600 leading-relaxed">{currentAnalysis.improvement_suggestion}</p>
                                    </div>

                                    <button className="w-full btn bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 py-4 text-sm font-bold" onClick={handleFix} disabled={isFixing}>
                                        {isFixing ? <Loader2 size={16} className="animate-spin text-indigo-600" /> : <Sparkles size={16} className="text-indigo-600" />}
                                        {isFixing ? 'กำลังปรับปรุง...' : 'ให้ AI ช่วยคำนวณข้อสอบใหม่'}
                                    </button>

                                    <button className="w-full btn bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 py-4 text-sm font-bold" onClick={handleSave} disabled={saveStatus !== 'idle'}>
                                        {saveStatus === 'saving' ? <Loader2 size={16} className="animate-spin" /> : (
                                            <div className="flex items-center gap-2">
                                                {saveStatus === 'saved' ? <CheckCircle size={16} className="text-green-600" /> : <Bookmark size={16} className="text-indigo-600" />}
                                                {saveStatus === 'saved' ? 'บันทึกลงคลังแล้ว' : 'บันทึกเข้าคลังข้อสอบ'}
                                            </div>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const Dashboard = ({ results, questions, filename, onBack }) => {
    const [isExporting, setIsExporting] = useState(null);

    const handleExport = async (format) => {
        setIsExporting(format);
        try {
            const response = await axios.post(`http://localhost:8000/api/export/${format}`, results, { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${filename?.split('.')[0] || 'exam_report'}.${format === 'excel' ? 'xlsx' : 'docx'}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            alert("ไม่สามารถส่งออกไฟล์ได้");
        } finally { setIsExporting(null); }
    };

    const stats = {
        total: results.length,
        good: results.filter(r => r.is_good_question).length,
        needsFix: results.length - results.filter(r => r.is_good_question).length
    };

    const bloomData = Object.entries(
        results.reduce((acc, r) => {
            const label = BLOOM_TH[r.bloom_level] || r.bloom_level;
            acc[label] = (acc[label] || 0) + 1;
            return acc;
        }, {})
    ).map(([name, value]) => ({ name, value }));

    return (
        <div className="container mx-auto px-8 mt-12 animate-fade">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                <div>
                    <button onClick={onBack} className="flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-bold text-sm mb-4">
                        <ArrowLeft size={16} /> กลับไปเริ่มวิเคราะห์ใหม่
                    </button>
                    <h1 className="text-4xl font-bold text-slate-900 tracking-tight">สรุปผลการวิเคราะห์ข้อสอบ</h1>
                    <p className="text-slate-500 mt-2">ชุดข้อสอบ: <span className="text-slate-800 font-bold">{filename || 'ไม่ระบุชื่อ'}</span></p>
                </div>
                <div className="flex gap-2">
                    <button className="btn bg-green-600 text-white hover:bg-green-700 shadow-sm" onClick={() => handleExport('excel')} disabled={isExporting}>
                        <FileSpreadsheet size={18} /> ส่งออก Excel
                    </button>
                    <button className="btn bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm" onClick={() => handleExport('word')} disabled={isExporting}>
                        <FileText size={18} /> ส่งออก Word
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-10 text-center">
                <div className="bg-white p-6 rounded-2xl border border-slate-100">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">จำนวนข้อทั้งหมด</p>
                    <h2 className="text-4xl font-extrabold text-slate-800">{stats.total}</h2>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 border-b-4 border-b-green-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">ที่ผ่านเกณฑ์คุณภาพ</p>
                    <h2 className="text-4xl font-extrabold text-green-600">{stats.good}</h2>
                </div>
                <div className="bg-white p-6 rounded-2xl border border-slate-100 border-b-4 border-b-yellow-500">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">ที่ควรปรับปรุง</p>
                    <h2 className="text-4xl font-extrabold text-yellow-600">{stats.needsFix}</h2>
                </div>
                <div className="bg-indigo-600 p-6 rounded-2xl text-white shadow-lg shadow-indigo-100">
                    <p className="text-[10px] font-bold opacity-70 uppercase tracking-widest mb-1 text-white">คะแนนเฉลี่ยชุดข้อสอบ</p>
                    <h2 className="text-4xl font-extrabold">{stats.total > 0 ? Math.round((stats.good / stats.total) * 100) : 0}%</h2>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-1">
                    <div className="bg-white p-8 rounded-3xl border border-slate-100 sticky top-8 shadow-sm">
                        <h3 className="text-lg font-bold mb-8 flex items-center gap-2">
                            <LayoutDashboard size={20} className="text-indigo-600" /> สัดส่วนพฤติกรรมการเรียนรู้
                        </h3>
                        <div className="h-60">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={bloomData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={75} paddingAngle={2}>
                                        {bloomData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={BLOOM_COLORS[Object.keys(BLOOM_TH).find(key => BLOOM_TH[key] === entry.name)] || '#94a3b8'} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ background: '#fff', border: 'none', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.08)' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-8 space-y-2">
                            {bloomData.map((entry, i) => (
                                <div key={i} className="flex justify-between items-center text-sm p-2.5 rounded-xl hover:bg-slate-50 transition-colors">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2.5 h-2.5 rounded-full" style={{ background: BLOOM_COLORS[Object.keys(BLOOM_TH).find(key => BLOOM_TH[key] === entry.name)] }} />
                                        <span className="text-slate-600 font-medium">{entry.name}</span>
                                    </div>
                                    <span className="font-bold text-slate-800">{entry.value} ข้อ</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-2">
                    <div className="bg-indigo-50/50 p-6 rounded-2xl border border-indigo-100 mb-8 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center">
                                <Sparkles size={20} className="text-white" />
                            </div>
                            <div>
                                <h4 className="font-bold text-slate-800 text-sm">คำแนะนำจากผู้เชี่ยวชาญ</h4>
                                <p className="text-xs text-slate-500">คุณสามารถคลิกที่แต่ละข้อเพื่อดูรายละเอียดการปรับปรุงแบบเจาะจง</p>
                            </div>
                        </div>
                    </div>
                    <div>
                        {results.map((r, i) => (
                            <QuestionCard key={i} question={r} index={i} originalText={questions[i]} filename={filename} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
