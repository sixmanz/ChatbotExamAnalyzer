import React, { useState } from 'react';
import { BookOpen, GraduationCap, ClipboardCheck, Sparkles, PlusCircle, History as HistoryIcon, LayoutDashboard } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import FileUpload from './components/FileUpload';
import Dashboard from './components/Dashboard';
import History from './components/History';

// --- Components ---

const Navbar = ({ onHome, onHistory, currentView }) => (
  <nav className="container mx-auto px-8 py-5 flex justify-between items-center relative z-10">
    <div className="flex items-center gap-3 cursor-pointer" onClick={onHome}>
      <div className="w-10 h-10 bg-indigo-600 flex items-center justify-center rounded-xl shadow-lg shadow-indigo-200">
        <GraduationCap size={24} className="text-white" />
      </div>
      <h2 className="text-xl font-bold m-0 tracking-tight text-slate-800">
        AI <span className="text-indigo-600">Teacher</span> Assistant
      </h2>
    </div>
    <div className="flex gap-4 items-center">
      <button
        className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${currentView === 'landing' ? 'text-indigo-600 bg-indigo-50' : 'text-slate-500 hover:text-indigo-600'}`}
        onClick={onHome}
      >
        หน้าหลัก
      </button>
      <button
        className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${currentView === 'history' ? 'text-indigo-600 bg-indigo-50' : 'text-slate-500 hover:text-indigo-600'}`}
        onClick={onHistory}
      >
        <BookOpen size={16} /> คลังข้อสอบ
      </button>
    </div>
  </nav>
);

const App = () => {
  const [view, setView] = useState('landing'); // landing, upload, analysis, history
  const [analysisData, setAnalysisData] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentFilename, setCurrentFilename] = useState("");

  const handleAnalysisComplete = (data, qs, fname) => {
    setAnalysisData(data);
    setQuestions(qs);
    setCurrentFilename(fname);
    setView('analysis');
  };

  return (
    <div className="relative min-h-screen bg-bg-main">
      <Navbar
        onHome={() => setView('landing')}
        onHistory={() => setView('history')}
        currentView={view}
      />

      <main className="pb-20">
        <AnimatePresence mode="wait">
          {view === 'landing' && (
            <motion.div
              key="landing"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
              className="container mx-auto px-8 pt-12"
            >
              <div className="max-w-4xl mx-auto text-center border-b border-slate-200 pb-16">
                <span className="section-badge">✨ เครื่องมือช่วยสอนยุคใหม่</span>
                <h1 className="text-5xl lg:text-6xl mt-4 mb-6 leading-tight text-slate-900">
                  วิเคราะห์คุณภาพข้อสอบของคุณ <br />
                  <span className="text-indigo-600 font-extrabold italic">ให้แม่นยำและเป็นมาตรฐาน</span>
                </h1>
                <p className="text-slate-600 text-lg max-w-2xl mx-auto mb-10 leading-relaxed">
                  ช่วยคุณครูตรวจสอบประเมินคุณภาพข้อสอบ (Item Analysis) ตามหลักวิชาการ
                  ให้ทุกข้อสอบมีคุณภาพและสอดคล้องกับมาตรฐานการเรียนรู้อย่างง่ายดาย
                </p>

                <div className="flex justify-center gap-4">
                  <button className="btn btn-primary px-8" onClick={() => setView('upload')}>
                    <PlusCircle size={20} /> เริ่มการวิเคราะห์ใหม่
                  </button>
                  <button className="btn glass px-8 text-slate-700 hover:border-indigo-200" onClick={() => setView('history')}>
                    <BookOpen size={20} className="text-indigo-600" /> เปิดคลังข้อสอบเดิม
                  </button>
                </div>
              </div>

              <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  { icon: <ClipboardCheck className="text-indigo-600" />, title: "สกัดข้อสอบอัตโนมัติ", desc: "รองรับไฟล์ PDF, Word และรูปภาพ ช่วยให้คุณไม่ต้องพิมพ์ข้อสอบใหม่เอง" },
                  { icon: <Sparkles className="text-indigo-600" />, title: "ประเมินระดับ Bloom", desc: "วิเคราะห์ระดับพฤติกรรมการเรียนรู้อย่างแม่นยำตามหลักการวัดผล" },
                  { icon: <GraduationCap className="text-indigo-600" />, title: "ปรับปรุงคุณภาพให้ดีขึ้น", desc: "AI ช่วยแนะนำการปรับโจทย์และตัวเลือกให้มีคุณภาพและยุติธรรม" }
                ].map((f, i) => (
                  <div key={i} className="glass p-8 hover:shadow-md hover:border-indigo-100 transition-all group">
                    <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                      {f.icon}
                    </div>
                    <h3 className="text-xl font-bold mb-3 text-slate-800">{f.title}</h3>
                    <p className="text-slate-500 text-sm leading-relaxed">{f.desc}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {view === 'upload' && (
            <motion.div key="upload" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <FileUpload
                onAnalysisComplete={handleAnalysisComplete}
                onBack={() => setView('landing')}
              />
            </motion.div>
          )}

          {view === 'analysis' && analysisData && (
            <motion.div key="analysis" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Dashboard
                results={analysisData}
                questions={questions}
                filename={currentFilename}
                onBack={() => setView('upload')}
              />
            </motion.div>
          )}

          {view === 'history' && (
            <motion.div key="history" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <History onSelect={handleAnalysisComplete} onBack={() => setView('landing')} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="container mx-auto px-8 mt-16 pb-12 text-center border-t border-slate-100">
        <p className="text-slate-400 text-xs mt-8 font-medium">
          © 2026 AI Teacher Assistant. เพื่อยกระดับมาตรฐานคุณภาพการศึกษาไทย
        </p>
      </footer>
    </div>
  );
};

export default App;
