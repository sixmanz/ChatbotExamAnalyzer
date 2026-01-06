
import re
import os

file_path = "c:\\Users\\LOQ\\Documents\\ChatbotExamAnalyzer\\app.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Define new functions string
new_functions_code = """
def render_top_navigation():
    \"\"\"Show Top Navigation Bar (Settings & Manual)\"\"\"
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 1, 1.5, 2])
        
        with col1:
            # Language
            st.button(
                t('language_btn'), 
                on_click=toggle_language,
                use_container_width=True,
                key='top_lang_toggle'
            )
            
        with col2:
            # Manual Popover/Expander
            with st.expander("📚 คู่มือ", expanded=False):
                st.markdown(t('tip_1'))
                st.markdown(t('tip_2'))
                st.markdown("---")
                st.markdown(t('quota_warning'))

        with col3:
            # Provider Selector
            provider_options = list(AI_PROVIDERS.keys())
            current_idx = provider_options.index(st.session_state.selected_provider) if st.session_state.selected_provider in provider_options else 0
            
            new_provider = st.selectbox(
                "AI Provider",
                options=provider_options,
                index=current_idx,
                key='top_provider',
                label_visibility="collapsed"
            )
            
            if new_provider != st.session_state.selected_provider:
                st.session_state.selected_provider = new_provider
                # Reset model
                first_model = list(AI_PROVIDERS[new_provider]["models"].keys())[0]
                st.session_state.selected_model = first_model
                st.session_state.analysis_results = None
                st.rerun()

        with col4:
            # Model Selector
            model_options = list(AI_PROVIDERS[st.session_state.selected_provider]["models"].keys())
            current_midx = model_options.index(st.session_state.selected_model) if st.session_state.selected_model in model_options else 0
            
            new_model = st.selectbox(
                "Model",
                options=model_options,
                index=current_midx,
                key='top_model',
                label_visibility="collapsed"
            )
            
            if new_model != st.session_state.selected_model:
                st.session_state.selected_model = new_model
                st.session_state.analysis_results = None

def render_sidebar_history():
    \"\"\"Show History in Sidebar\"\"\"
    st.header("📜 ประวัติการวิเคราะห์")
    history = load_analysis_history()
    
    if not history:
        st.info("ยังไม่มีประวัติ")
        return

    # Show latest first
    for i, entry in enumerate(reversed(history)):
        timestamp = entry.get('timestamp', 'N/A')
        filename = entry.get('filename', 'Unknown')
        
        # Format nice timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%d/%m %H:%M")
        except:
            time_str = timestamp

        if st.button(f"{time_str} - {filename}", key=f"hist_btn_{i}", use_container_width=True):
            st.session_state.analysis_results = entry.get('results')
            st.session_state.question_texts = entry.get('question_texts') # Optional restore
            st.success(f"โหลดประวัติ: {filename}")
            st.rerun()
"""

# 2. Insert functions BEFORE main
if "def main():" in content and "def render_top_navigation():" not in content:
    content = content.replace("def main():", new_functions_code + "\n\ndef main():")
    print("Inserted new functions definition.")

# 3. Replace Sidebar Logic with History Logic
# Find start of sidebar
start_marker = "with st.sidebar:"
match_start = content.find(start_marker)

if match_start != -1:
    # We want to replace everything from `with st.sidebar:` down to where sidebar logic ends.
    # We previously identified it ends around `st.error(t('api_warning'))`
    end_marker = "st.error(t('api_warning'))"
    match_end = content.find(end_marker, match_start)
    
    if match_end != -1:
        # Find newline after match_end
        line_end_pos = content.find("\n", match_end)
        
        new_sidebar_block = """    with st.sidebar:
        render_sidebar_history()
"""
        content = content[:match_start] + new_sidebar_block + content[line_end_pos:]
        print("Replaced Sidebar with History.")
    else:
        print("Could not find end of Sidebar block.")
else:
    print("Could not find Sidebar block.")


# 4. Insert Top Nav Call
# Look for Header or similar near start of main
# `st.markdown(f"\"\"` usually starts the header.
header_start_marker = 'st.markdown(f"""'
idx_header = content.find(header_start_marker)
# Also check for alternate quote style if I fixed it previously
if idx_header == -1:
    idx_header = content.find('st.markdown(f"\"\"')

if idx_header != -1:
    # Insert render_top_navigation() call
    content = content[:idx_header] + "    render_top_navigation()\n    st.markdown('---')\n    " + content[idx_header:]
    print("Inserted render_top_navigation() call.")
else:
    print("Could not find Header start.")


# 5. Move Custom Prompt back to Main
# Logic: Find Sidebar Custom Prompt -> Remove -> Insert into Main
cp_marker = "# --- Custom Prompt (Sidebar) ---"
start_cp = content.find(cp_marker)

if start_cp != -1:
    # Find end. `st.info(t('custom_prompt_default'))`
    end_cp_marker = "st.info(t('custom_prompt_default'))"
    idx_end_cp = content.find(end_cp_marker, start_cp)
    
    if idx_end_cp != -1:
        # Include newline
        end_cp_pos = content.find("\n", idx_end_cp)
        
        # Remove from sidebar (now strictly speaking it might be gone if Step 3 replaced the WHOLE sidebar block?)
        # WAIT! If Step 3 replaced the *entire* sidebar block from `with st.sidebar:` to `api_warning`, 
        # DID Custom Prompt reside IN that block?
        # Yes! In Step 989, I inserted it *inside* sidebar (after Model info).
        # So Step 3 replacement might have DESTROYED Custom Prompt logic entirely!
        # Which is GOOD! I wanted to move it anyway.
        # But wait, if Step 3 ran BEFORE Step 5, then `start_cp` check in Step 5 will FAIL (not found).
        # So I only need to INSERT it into Main.
        
        # Let's check order.
        # I execute logic on `content` string sequentially.
        # Step 3 replaced the sidebar block. If Custom Prompt was inside that range, it's GONE from `content`.
        # So I just need to Insert into Main.
        
        pass # Already removed by Step 3

else:
    # If not found (maybe sidebar replacement killed it), we just insert into Main.
    pass

# INSERT Custom Prompt into Main
# Find Step 1
step1_marker = "st.header(t('step1_title'))"
idx_step1 = content.find(step1_marker)

if idx_step1 != -1:
    # Find insertion point (before st.markdown("---") preceding Step 1 if possible)
    # Check 50 chars back
    pre_context = content[max(0, idx_step1-50):idx_step1]
    insert_pos = idx_step1
    if 'st.markdown("---")' in pre_context:
        # Insert before that HR
        last_hr = content.rfind('st.markdown("---")', 0, idx_step1)
        if last_hr != -1:
            insert_pos = last_hr
            
    new_cp_block = """
    # --- Custom Prompt (Main) ---
    st.markdown("---")
    with st.expander(t('custom_prompt_title'), expanded=False):
        st.markdown(f"**{t('custom_prompt_label')}**")
        custom_prompt_input = st.text_area(
            "Custom Prompt",
            value=st.session_state.custom_prompt,
            height=150,
            placeholder=t('custom_prompt_placeholder'),
            key='custom_prompt_main',
            label_visibility="collapsed"
        )
        if custom_prompt_input != st.session_state.custom_prompt:
            st.session_state.custom_prompt = custom_prompt_input
            st.session_state.analysis_results = None
        
        col_status1, col_status2 = st.columns([1, 1])
        with col_status1:
            if st.session_state.custom_prompt.strip():
                st.success(t('custom_prompt_active'))
            else:
                st.info(t('custom_prompt_default'))
"""
    content = content[:insert_pos] + new_cp_block + "\n" + content[insert_pos:]
    print("Inserted Custom Prompt into Main.")
else:
    print("Could not find Step 1.")

# Write result
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
