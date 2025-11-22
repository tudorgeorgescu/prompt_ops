import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
# --- Configuration ---
PROMPTS_FILE = 'prompts.json'
INPUT_FILE = 'source_data.csv'
OUTPUT_FILE = 'batch_results.csv'
# --- 1. Data Management Functions ---
def load_data():
    """Simulates reading from a Table/Database"""
    # Load Input Data
    if os.path.exists(INPUT_FILE):
        df_input = pd.read_csv(INPUT_FILE)
    else:
        st.error(f"Input file {INPUT_FILE} not found!")
        df_input = pd.DataFrame()
    # Load Prompts
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            prompts_data = json.load(f)
    else:
        prompts_data = []
    return df_input, prompts_data
def save_prompts(prompts_list):
    """Simulates writing to a Database"""
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts_list, f, indent=2)
def mock_llm_call(prompt_text):
    """
    Simulates calling an LLM API (OpenAI/Anthropic/Databricks).
    Replace this with your actual API call.
    """
    time.sleep(0.1) # Simulate network latency
    return f"SIMULATED LLM RESPONSE: Based on '{prompt_text[:30]}...', I suggest checking the warranty."
# --- 2. The "Batch Job" Logic ---
def run_batch_job():
    df_input, prompts_data = load_data()
    # Find active prompt
    active_prompt = next((p for p in prompts_data if p['is_active']), None)
    if not active_prompt:
        return None, "No active prompt found!"
    results = []
    template = active_prompt['template']
    progress_bar = st.progress(0)
    for index, row in df_input.iterrows():
        try:
            # Dynamic Injection using Python's format **kwargs
            # This replaces {col_name} in text with row['col_name']
            full_prompt = template.format(**row.to_dict())
            # Call AI
            response = mock_llm_call(full_prompt)
            results.append({
                "customer_id": row.get('customer_id', index),
                "prompt_version": active_prompt['id'],
                "full_prompt_sent": full_prompt,
                "llm_output": response,
                "processed_at": datetime.now().isoformat()
            })
        except KeyError as e:
            return None, f"Error: Template variable {e} not found in input CSV columns."
        progress_bar.progress((index + 1) / len(df_input))
    # Save Results
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_FILE, index=False)
    return df_results, "Success"
# --- 3. The Streamlit UI ---
st.set_page_config(layout="wide", page_title="Cloud Prompt Manager")
# Load Data
df_source, prompts_list = load_data()
available_columns = df_source.columns.tolist()
st.title(":zap: Cloud Prompt Ops")
st.markdown("Manage prompts and run batch inference without Databricks.")
# --- Sidebar: Data Context ---
with st.sidebar:
    st.header("Data Context")
    st.caption(f"Source: {INPUT_FILE}")
    st.write("**Available Variables:**")
    for col in available_columns:
        st.code(f"{{{col}}}")
    st.divider()
    st.write("**Batch Output**")
    if os.path.exists(OUTPUT_FILE):
        st.success("Results file exists.")
        with open(OUTPUT_FILE, "rb") as file:
            st.download_button("Download Results CSV", file, "results.csv")
    else:
        st.warning("No results yet.")
# --- Main Interface ---
tab1, tab2 = st.tabs([":memo: Prompt Editor", ":rocket: Batch Runner"])
# TAB 1: EDIT PROMPTS
with tab1:
    col_list, col_edit = st.columns([1, 2])
    # Prompt Selector
    with col_list:
        st.subheader("Select Prompt")
        prompt_names = [p['name'] for p in prompts_list] + ["+ Create New"]
        # Helper to get current index
        selected_name = st.radio("Prompts", prompt_names)
        selected_data = next((p for p in prompts_list if p['name'] == selected_name), None)
    # Editor Form
    with col_edit:
        st.subheader("Edit Configuration")
        with st.form("edit_form"):
            if selected_data:
                f_id = st.text_input("ID", value=selected_data['id'], disabled=True)
                f_name = st.text_input("Name", value=selected_data['name'])
                f_active = st.checkbox("Active for Batch", value=selected_data['is_active'])
                f_template = st.text_area("Template", value=selected_data['template'], height=250)
            else:
                f_id = st.text_input("ID (Unique)", value=f"prompt_{int(time.time())}")
                f_name = st.text_input("Name", value="New Prompt")
                f_active = st.checkbox("Active for Batch", value=False)
                f_template = st.text_area("Template", placeholder="Hello {customer_name}...", height=250)
            if st.form_submit_button("Save Changes"):
                # Logic to update the list
                new_entry = {
                    "id": f_id,
                    "name": f_name,
                    "template": f_template,
                    "is_active": f_active,
                    "updated_at": datetime.now().isoformat()
                }
                # If editing existing, replace it. If new, append.
                if selected_data:
                    index = prompts_list.index(selected_data)
                    prompts_list[index] = new_entry
                else:
                    prompts_list.append(new_entry)
                # Ensure only one is active (optional logic)
                if f_active:
                    for p in prompts_list:
                        if p['id'] != f_id: p['is_active'] = False
                save_prompts(prompts_list)
                st.success("Saved!")
                st.rerun()
# TAB 2: RUN BATCH
with tab2:
    st.header("Manual Batch Execution")
    st.write("This replaces the Databricks Workflow schedule.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"Input Rows: {len(df_source)}")
    with col_b:
        active = next((p for p in prompts_list if p['is_active']), None)
        if active:
            st.success(f"Active Prompt: {active['name']}")
        else:
            st.error("No active prompt selected.")
    if st.button("Run Batch Job Now", type="primary", disabled=not active):
        with st.spinner("Processing rows..."):
            df_result, msg = run_batch_job()
            if df_result is not None:
                st.success("Batch Complete!")
                st.dataframe(df_result)
            else:
                st.error(msg)
