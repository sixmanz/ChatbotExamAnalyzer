import streamlit as st

def load_custom_css():
    """Injects custom CSS for an Ultra-Minimalist, Clean look."""
    
    st.markdown("""
    <style>
        /* Import Font: Sarabun & Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Sarabun:wght@300;400;500;600&display=swap');

        /* --- 1. Global Reset & Typography --- */
        html, body, [class*="css"] {
            font-family: 'Sarabun', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #2D3748; /* Dark Gray text for softness (vs pure black) */
        }
        
        /* Background: Clean Off-White */
        .stApp {
            background-color: #FAFAFA; /* Very light gray */
            background-image: none; /* Remove gradients */
        }

        /* --- 2. Containers & Cards (Minimalist) --- */
        /* Remove borders, use soft shadows */
        div[data-testid="stMetric"], 
        div[data-testid="stExpander"], 
        div.stContainer {
            background-color: #FFFFFF;
            border: none;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03); /* Extremely subtle shadow */
            padding: 1.5rem;
            transition: box-shadow 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.06);
        }

        /* Expander Header Clean up */
        .streamlit-expanderHeader {
            background-color: transparent;
            font-weight: 500;
            color: #4A5568;
        }

        /* --- 3. Buttons (Flat & Sophisticated) --- */
        div.stButton > button:first-child {
            background: #4F46E5; /* Indigo-600 */
            color: white;
            border: none;
            border-radius: 8px; /* Slightly tighter radius */
            padding: 0.5rem 1rem;
            font-weight: 500;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
        }

        div.stButton > button:first-child:hover {
            background: #4338CA; /* Indigo-700 */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateY(-1px);
        }

        div.stButton > button:first-child:active {
            transform: translateY(0);
        }

        /* Secondary Button (Ghost) */
        button[kind="secondary"] {
            background: transparent;
            border: 1px solid #E2E8F0;
            color: #4A5568;
        }

        /* --- 4. Inputs (Clean) --- */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.5rem;
            color: #2D3748;
        }
        
        .stTextInput > div > div > input:focus, 
        .stTextArea > div > div > textarea:focus {
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        /* --- 5. Custom Elements --- */
        /* Headers */
        h1 {
            color: #1A202C;
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        h2, h3, h4 {
            color: #2D3748;
            font-weight: 500;
        }

        /* Spinner Color */
        .stSpinner > div {
            border-top-color: #4F46E5 !important;
        }

        /* Toast */
        div[data-testid="stToast"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-radius: 10px;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #EDF2F7; 
        }
        ::-webkit-scrollbar-thumb {
            background: #CBD5E0; 
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #A0AEC0; 
        }

    </style>
    """, unsafe_allow_html=True)
