# 🎨 Shadcn/Vercel Inspired CSS - Premium Modern Design
SHADCN_CSS = """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sarabun:wght@300;400;500;600;700&display=swap');

:root {
    --background: #ffffff;
    --foreground: #0f172a;
    --muted: #f8fafc;
    --muted-foreground: #64748b;
    --border: #e2e8f0;
    --ring: #6366f1; /* Indigo-500 */
    --primary: #0f172a; /* Slate-900 */
    --primary-foreground: #f8fafc;
    --radius: 0.75rem; /* 12px rounded */
    --font-sans: 'Inter', 'Sarabun', system-ui, -apple-system, sans-serif;
}

/* Global Reset */
.stApp {
    background-color: var(--background);
    font-family: var(--font-sans);
    color: var(--foreground);
    line-height: 1.6;
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-sans);
    letter-spacing: -0.025em;
    color: var(--foreground) !important;
}

h1 { font-weight: 800 !important; font-size: 2.25rem !important; }
h2 { font-weight: 700 !important; font-size: 1.5rem !important; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-top: 2rem; }
h3 { font-weight: 600 !important; font-size: 1.125rem !important; }

/* 🌟 Premium Buttons */
.stButton > button {
    background: var(--primary);
    color: var(--primary-foreground) !important;
    border: 1px solid transparent;
    border-radius: var(--radius);
    padding: 0.625rem 1.25rem;
    font-weight: 600;
    font-size: 0.95rem;
    box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.1), 0 2px 4px -2px rgba(15, 23, 42, 0.1);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.stButton > button:hover {
    background: #1e293b; /* Slate-800 */
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.1), 0 4px 6px -4px rgba(15, 23, 42, 0.1);
}

.stButton > button:active {
    transform: translateY(0);
}

/* 🎨 Modern Inputs & Selects */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stMultiSelect > div > div > div {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important; /* Slate-300 */
    border-radius: var(--radius) !important;
    color: var(--foreground) !important;
    font-size: 0.95rem !important;
    padding: 0.5rem 0.75rem !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--ring) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important; /* Indigo glow */
    outline: none;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #f8fafc; /* Slate-50 */
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #334155 !important; /* Slate-700 */
}

/* Secondary Buttons (in Sidebar usually) */
[data-testid="stSidebar"] .stButton > button {
    background: white;
    color: #475569 !important; /* Slate-600 */
    border: 1px solid #cbd5e1;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #f1f5f9;
    color: #0f172a !important;
    border-color: #94a3b8;
}

/* File Uploader - Drag & Drop Area */
[data-testid="stFileUploader"] section {
    background-color: #ffffff;
    border: 2px dashed #cbd5e1;
    border-radius: 1rem;
    padding: 2.5rem;
    transition: all 0.2s ease;
}

[data-testid="stFileUploader"] section:hover {
    border-color: var(--ring);
    background-color: #f8fafc;
}

/* Cards / Containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff;
    border: 1px solid var(--border);
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* Custom Success/Error/Info Alerts */
.stSuccess, .stError, .stWarning, .stInfo {
    border-radius: 0.75rem;
    border: none;
    padding: 1rem 1.25rem;
}

.stSuccess { background-color: #dcfce7 !important; color: #166534 !important; }
.stError { background-color: #fee2e2 !important; color: #991b1b !important; }
.stWarning { background-color: #fef3c7 !important; color: #92400e !important; }
.stInfo { background-color: #eff6ff !important; color: #1e40af !important; }

/* Expanders */
.streamlit-expanderHeader {
    background-color: white !important;
    border: 1px solid var(--border) !important;
    border-radius: 0.75rem !important;
    padding: 1rem !important;
    font-weight: 600;
}

.streamlit-expanderContent {
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 0.75rem 0.75rem;
    padding: 1.5rem !important;
    background-color: #f8fafc;
}

/* Clean up Streamlit cruft */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
"""
