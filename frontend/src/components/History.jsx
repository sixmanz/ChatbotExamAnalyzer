import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, FileText, ChevronRight, Loader2, Calendar, Trash2, BookOpen, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const History = ({ onSelect, onBack }) => {
    const [history, setHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isDeleting, setIsDeleting] = useState(null);
    const [searchTerm, setSearchTerm] = useState("");

    const fetchHistory = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/history');
            setHistory(response.data);
        } catch (err) {
            console.error("Failed to fetch history");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const handleDelete = async (e, id) => {
        e.stopPropagation();
        if (!window.confirm("ยืนยันการลบประวัติการวิเคราะห์ชุดนี้?")) return;
        setIsDeleting(id);
        try {
            await axios.delete(`http://localhost:8000/api/history/${id}`);
            setHistory(prev => prev.filter(item => item.id !== id));
        } catch (err) {
            alert("ไม่สามารถลบข้อมูลได้");
        } finally {
            setIsDeleting(null);
        }
    };

    const handleClearAll = async () => {
        if (!window.confirm("คำเตือน: นี่จะเป็นการลบประวัติทั้งหมดออกจากระบบอย่างถาวร ต้องการดำเนินการต่อหรือไม่?")) return;
        setIsLoading(true);
        try {
            await axios.delete('http://localhost:8000/api/history');
            setHistory([]);
        } catch (err) {
            alert("ไม่สามารถล้างคลังข้อสอบได้");
        } finally {
            setIsLoading(false);
        }
    };

    const filteredHistory = history.filter(item =>
        item.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (isLoading && history.length === 0) {
        return (
            <div className="container mx-auto px-8 text-center py-40 animate-fade">
                <Loader2 className="animate-spin mx-auto text-indigo-600 mb-4" size={48} />
                <p className="text-slate-500 font-medium tracking-wide">กำลังเปิดคลังข้อสอบของคุณ...</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-8 mt-12 max-w-5xl animate-fade">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-12">
                <div>
                    <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">คลังเก็บ <span className="text-indigo-600">ประมวลผลข้อสอบ</span></h1>
                    <p className="text-slate-500 mt-2 text-lg font-medium">รวมประวัติการวิเคราะห์และคุณภาพข้อสอบที่คุณเคยทำไว้</p>
                </div>
                <div className="flex gap-2">
                    {history.length > 0 && (
                        <button
                            onClick={handleClearAll}
                            className="px-4 py-2 text-xs font-bold text-red-500 hover:bg-red-50 rounded-xl transition-all border border-red-100"
                        >
                            <Trash2 size={14} className="inline mr-1" /> ล้างคลังข้อสอบทั้งหมด
                        </button>
                    )}
                </div>
            </div>

            <div className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden min-h-[400px]">
                <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex items-center gap-4">
                    <Search className="text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="ค้นหาชื่อไฟล์ข้อสอบ..."
                        className="bg-transparent border-none focus:outline-none text-sm w-full font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="flex flex-col">
                    <AnimatePresence>
                        {filteredHistory.length === 0 ? (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="py-20 text-center">
                                <BookOpen size={48} className="text-slate-200 mx-auto mb-4" />
                                <p className="text-slate-400 font-medium">ไม่พบประวัติการวิเคราะห์ในคลัง</p>
                            </motion.div>
                        ) : (
                            filteredHistory.map((item) => (
                                <motion.div
                                    key={item.id}
                                    layout
                                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                    className="p-6 flex items-center justify-between gap-6 cursor-pointer hover:bg-slate-50 transition-all border-b border-slate-50 last:border-none group shadow-sm hover:shadow-indigo-50"
                                    onClick={() => {
                                        const res = JSON.parse(item.raw_results);
                                        const qs = res.map(r => r.question_text || "");
                                        onSelect(res, qs, item.filename);
                                    }}
                                >
                                    <div className="flex items-center gap-5 flex-1 min-w-0">
                                        <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center shrink-0 group-hover:bg-indigo-600 transition-all duration-300">
                                            <FileText size={20} className="text-indigo-600 group-hover:text-white" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-bold text-slate-800 mb-1 truncate group-hover:text-indigo-600 transition-colors uppercase tracking-tight text-base">{item.filename}</h4>
                                            <div className="flex items-center gap-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                                <span className="flex items-center gap-1"><Calendar size={12} /> {new Date(item.timestamp).toLocaleDateString('th-TH', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                                                <span className="flex items-center gap-1"><Clock size={12} /> {item.total_questions} ข้อ</span>
                                                <span className="text-green-600 bg-green-50 px-2 py-0.5 rounded-full">{item.good_questions} ผ่านเกณฑ์</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={(e) => handleDelete(e, item.id)}
                                            className="p-2 text-slate-300 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100"
                                            disabled={isDeleting === item.id}
                                        >
                                            {isDeleting === item.id ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                                        </button>
                                        <ChevronRight size={20} className="text-slate-200 group-hover:text-indigo-600 transition-all" />
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <div className="text-center mt-12">
                <button onClick={onBack} className="text-sm font-bold text-slate-400 hover:text-indigo-600 transition-colors">
                    ← กลับหน้าหลัก
                </button>
            </div>
        </div>
    );
};

export default History;
