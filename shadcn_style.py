# 🎨 Shadcn/Tailwind Inspired CSS - Minimal Clean Design
SHADCN_CSS = """
<style>
/* Import Google Fonts - Inter (main) + Sarabun (Thai) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sarabun:wght@300;400;500;600;700&display=swap');

/* ===== CSS VARIABLES (Shadcn/Tailwind Style) ===== */
:root {
    --background: #ffffff;
    --foreground: #0f172a;
    --muted: #f1f5f9;
    --muted-foreground: #64748b;
    --border: #e2e8f0;
    --ring: #94a3b8;
    --primary: #18181b;
    --primary-foreground: #fafafa;
    --secondary: #f4f4f5;
    --secondary-foreground: #18181b;
    --radius: 8px;
    --font-sans: 'Inter', 'Sarabun', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ===== GLOBAL STYLES ===== */
.stApp {
    background: var(--background);
    font-family: var(--font-sans);
    color: var(--foreground);
    min-height: 100vh;
    line-height: 1.6;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ===== TYPOGRAPHY ===== */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-sans);
    font-weight: 600;
    letter-spacing: -0.02em;
    color: var(--foreground) !important;
}

h1 {
    font-size: 1.875rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem;
}

h2 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    margin-top: 1.5rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}

h3 {
    font-size: 1rem !important;
    font-weight: 500 !important;
}

p, span, label, .stMarkdown {
    color: var(--muted-foreground) !important;
    font-size: 0.875rem;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: var(--muted);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--foreground) !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
}

/* ===== MAIN CONTENT ===== */
.main .block-container {
    padding: 2rem 3rem;
    max-width: 900px;
}

/* ===== BUTTONS (Shadcn Style) ===== */
.stButton > button {
    background: var(--primary);
    color: var(--primary-foreground) !important;
    border: none;
    border-radius: var(--radius);
    padding: 0.5rem 1rem;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all 0.15s ease;
    box-shadow: none;
}

.stButton > button:hover {
    background: #27272a;
    transform: none;
}

.stButton > button:active {
    transform: scale(0.98);
}

/* Secondary buttons (sidebar) */
[data-testid="stSidebar"] .stButton > button {
    background: var(--secondary);
    color: var(--secondary-foreground) !important;
    border: 1px solid var(--border);
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #e4e4e7;
}

/* ===== INPUT FIELDS ===== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--background) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--foreground) !important;
    font-size: 0.875rem !important;
    transition: border-color 0.15s ease;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--ring) !important;
    box-shadow: 0 0 0 2px rgba(148, 163, 184, 0.2) !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] section {
    background: var(--muted);
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2rem;
}

[data-testid="stFileUploader"] section:hover {
    border-color: var(--ring);
}

/* ===== CARDS / CONTAINERS ===== */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--background) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
}

/* ===== METRICS ===== */
[data-testid="stMetric"] {
    background: var(--muted);
    border-radius: var(--radius);
    padding: 1rem;
    border: 1px solid var(--border);
}

[data-testid="stMetric"] label {
    color: var(--muted-foreground) !important;
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--foreground) !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid var(--border);
    gap: 0;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--muted-foreground);
    padding: 0.75rem 1rem;
    font-weight: 500;
    font-size: 0.875rem;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--foreground);
}

.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: var(--foreground) !important;
    border-bottom: 2px solid var(--foreground) !important;
}

/* ===== EXPANDERS ===== */
.streamlit-expanderHeader {
    background: var(--muted);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    color: var(--foreground) !important;
    font-weight: 500;
}

.streamlit-expanderHeader:hover {
    background: #e2e8f0;
}

.streamlit-expanderContent {
    background: var(--background);
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 var(--radius) var(--radius);
}

/* ===== DATAFRAMES ===== */
[data-testid="stDataFrame"] {
    background: var(--background);
    border-radius: var(--radius);
    border: 1px solid var(--border);
}

/* ===== ALERTS ===== */
.stSuccess {
    background: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    border-radius: var(--radius);
}

.stSuccess p, .stSuccess span {
    color: #166534 !important;
}

.stWarning {
    background: #fffbeb !important;
    border: 1px solid #fde68a !important;
    border-radius: var(--radius);
}

.stWarning p, .stWarning span {
    color: #92400e !important;
}

.stError {
    background: #fef2f2 !important;
    border: 1px solid #fecaca !important;
    border-radius: var(--radius);
}

.stError p, .stError span {
    color: #991b1b !important;
}

.stInfo {
    background: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius);
}

.stInfo p, .stInfo span {
    color: var(--foreground) !important;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div {
    background: var(--primary);
    border-radius: 9999px;
}

/* ===== DIVIDERS ===== */
hr {
    border: none;
    height: 1px;
    background: var(--border);
    margin: 1.5rem 0;
}

/* ===== CODE BLOCKS ===== */
.stCodeBlock {
    background: #18181b !important;
    border-radius: var(--radius);
    border: 1px solid #27272a;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--muted);
}

::-webkit-scrollbar-thumb {
    background: var(--ring);
    border-radius: 4px;
}

/* ===== STATUS WIDGET ===== */
[data-testid="stStatusWidget"] {
    background: var(--background);
    border-radius: var(--radius);
    border: 1px solid var(--border);
}
</style>
"""
