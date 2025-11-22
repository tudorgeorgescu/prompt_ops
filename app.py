import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import re

# --- Configuration ---
PROMPTS_FILE = 'prompts.json'
INPUT_FILE = 'source_data.csv'
SCHEMA_FILE = 'schema_config.json'
OUTPUT_FILE = 'batch_results.csv'

# --- 1. Data Management Functions ---

def load_data():
    """Reads CSV data, Prompt JSON, and Schema Descriptions"""
    # 1. Load CSV Data
    if os.path.exists(INPUT_FILE):
        df_input = pd.read_csv(INPUT_FILE)
    else:
        df_input = pd.DataFrame()

    # 2. Load Prompts
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            prompts_data = json.load(f)
    else:
        prompts_data = []

    # 3. Load Schema Descriptions
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'r') as f:
            schema_data = json.load(f)
    else:
        schema_data = {}
    
    return df_input, prompts_data, schema_data

def save_prompts(prompts_list):
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts_list, f, indent=2)

def mock_llm_call(prompt_text, model_name="gpt-mock"):
    time.sleep(0.05)
    return f"[{model_name}]: Response to '{prompt_text[:15]}...'"

# --- 2. Batch Logic ---
def run_batch_job(df_input, selected_prompts_list):
    results = []
    total_ops = len(df_input) * len(selected_prompts_list)
    progress_bar = st.progress(0)
    step = 0
    
    for prompt_config in selected_prompts_list:
        template = prompt_config['template']
        p_id = prompt_config['id']
        
        for index, row in df_input.iterrows():
            try:
                full_prompt = template.format(**row.to_dict())
                response = mock_llm_call(full_prompt)
                
                results.append({
                    "customer_id": row.get('customer_id', index),
                    "prompt_version": p_id,
                    "prompt_name": prompt_config['name'],
                    "full_prompt_sent": full_prompt,
                    "llm_output": response,
                    "processed_at": datetime.now().isoformat()
                })
            except KeyError as e:
                return None, f"Error in prompt '{p_id}': Variable {e} missing in CSV."
            
            step += 1
            progress_bar.progress(step / total_ops)

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_FILE, index=False)
    return df_results, f"Success! Generated {len(df_results)} outputs."

# --- 3. UI Setup ---

st.set_page_config(layout="wide", page_title="Cloud Prompt Ops")
st.title("⚡ Cloud Prompt A/B Tester")

df_source, prompts_list, schema_dict = load_data()

# ==========================
# SIDEBAR
# ==========================
with st.sidebar:
    st.header("Project Context")
    st.info(f"Loaded {len(df_source)} rows from `{INPUT_FILE}`")
    
    # --- MOVED: Parameter Reference Pane ---
    st.divider()
    with st.expander("📚 Available Data Parameters", expanded=False):
        st.markdown("Use these variables in your template:")
        
        cols = df_source.columns.tolist()
        doc_data = []
        for c in cols:
            doc_data.append({
                "Variable": f"{{{c}}}", 
                "Description": schema_dict.get(c, "-")
            })
        
        # Display as a dataframe (cleaner in sidebar than markdown list)
        st.dataframe(
            pd.DataFrame(doc_data), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Variable": st.column_config.TextColumn("Var", width="small"),
                "Description": st.column_config.TextColumn("Desc", width="medium"),
            }
        )
    # ---------------------------------------

    st.divider()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as file:
            st.download_button("📥 Download Results", file, "batch_results.csv")

# ==========================
# MAIN TABS
# ==========================
tab1, tab2 = st.tabs(["📝 Prompt Editor", "🚀 Batch Runner"])

# --- TAB 1: PROMPT EDITOR ---
with tab1:
    col_left, col_right = st.columns([1, 2])
    
    # 1. Selection (Left Column)
    with col_left:
        st.subheader("Select Prompt")
        options = [p['name'] for p in prompts_list] + ["+ Create New"]
        
        # Using segmented control as requested (requires Streamlit 1.31+)
        selected_name = st.radio(
            "Prompts", 
            options, 
            label_visibility="collapsed"
        )
        
        selected_data = next((p for p in prompts_list if p['name'] == selected_name), None)

    # 2. Editing (Right Column)
    with col_right:
        st.subheader("Edit Configuration")
        with st.form("edit_form"):
            if selected_data:
                f_id = st.text_input("ID", value=selected_data['id'], disabled=True)
                f_name = st.text_input("Name", value=selected_data['name'])
                f_active = st.checkbox("Active for Batch", value=selected_data.get('is_active', False))
                f_template = st.text_area("Template", value=selected_data['template'], height=300)
            else:
                f_id = st.text_input("ID", value=f"prompt_{int(time.time())}")
                f_name = st.text_input("Name", value="New Prompt")
                f_active = st.checkbox("Active for Batch", value=True)
                f_template = st.text_area("Template", placeholder="Analyze {customer_name}...", height=300)

            # Validation Preview
            if f_template:
                st.caption("Preview of variables detected:")
                vars_found = re.findall(r'\{(.*?)\}', f_template)
                valid_vars = [v for v in vars_found if v in df_source.columns]
                invalid_vars = [v for v in vars_found if v not in df_source.columns]
                
                if invalid_vars:
                    st.error(f"⚠️ Invalid variables: {invalid_vars}")
                elif valid_vars:
                    st.success(f"✅ Valid variables: {valid_vars}")

            if st.form_submit_button("Save Prompt"):
                new_entry = {
                    "id": f_id, "name": f_name, 
                    "template": f_template, 
                    "is_active": f_active,
                    "updated_at": datetime.now().isoformat()
                }
                if selected_data:
                    prompts_list[prompts_list.index(selected_data)] = new_entry
                else:
                    prompts_list.append(new_entry)
                
                save_prompts(prompts_list)
                st.success("Saved!")
                st.rerun()

# --- TAB 2: BATCH RUNNER ---
with tab2:
    st.header("Execute Batch")
    
    active_candidates = [p for p in prompts_list if p.get('is_active')]
    
    if not active_candidates:
        st.warning("No active prompts found.")
    else:
        st.write("Select prompts to run:")
        candidate_names = [p['name'] for p in active_candidates]
        selected_names = st.multiselect("Active Prompts", candidate_names, default=candidate_names)
        prompts_to_run = [p for p in active_candidates if p['name'] in selected_names]
        
        if st.button("🚀 Run Batch", type="primary", disabled=not prompts_to_run):
            with st.spinner("Running..."):
                df_result, msg = run_batch_job(df_source, prompts_to_run)
                if df_result is not None:
                    st.success(msg)
                    st.dataframe(df_result.head(10), use_container_width=True)
                else:
                    st.error(msg)



