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
    """Simulates reading from files"""
    if os.path.exists(INPUT_FILE):
        df_input = pd.read_csv(INPUT_FILE)
    else:
        df_input = pd.DataFrame()

    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            prompts_data = json.load(f)
    else:
        prompts_data = []
    
    return df_input, prompts_data

def save_prompts(prompts_list):
    """Saves prompts to JSON"""
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts_list, f, indent=2)

def mock_llm_call(prompt_text, model_name="gpt-mock"):
    """
    Simulated LLM Latency and Response.
    """
    time.sleep(0.05) # Tiny sleep to visualize progress bar
    return f"[{model_name}]: Response to '{prompt_text[:15]}...'"

# --- 2. The Multi-Prompt Batch Logic ---

def run_batch_job(df_input, selected_prompts_list):
    """
    Runs the input data against ALL selected prompts (Cross Join).
    """
    results = []
    
    # Create a progress bar
    total_operations = len(df_input) * len(selected_prompts_list)
    progress_bar = st.progress(0)
    current_step = 0
    
    # Loop 1: Iterate through the selected prompts
    for prompt_config in selected_prompts_list:
        template = prompt_config['template']
        p_id = prompt_config['id']
        
        # Loop 2: Iterate through the data rows
        for index, row in df_input.iterrows():
            try:
                # 1. Inject Variables
                full_prompt = template.format(**row.to_dict())
                
                # 2. Call LLM
                response = mock_llm_call(full_prompt)
                
                # 3. Store Result
                results.append({
                    "customer_id": row.get('customer_id', index),
                    "prompt_version": p_id, # Crucial for A/B testing
                    "prompt_name": prompt_config['name'],
                    "full_prompt_sent": full_prompt,
                    "llm_output": response,
                    "processed_at": datetime.now().isoformat()
                })
            except KeyError as e:
                return None, f"Error in prompt '{p_id}': Variable {e} missing in CSV."
            
            # Update UI
            current_step += 1
            progress_bar.progress(current_step / total_operations)

    # Save to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_FILE, index=False)
    
    return df_results, f"Success! Generated {len(df_results)} outputs."

# --- 3. The Streamlit UI ---

st.set_page_config(layout="wide", page_title="Cloud Prompt Ops")
st.title("⚡ Cloud Prompt A/B Tester")

df_source, prompts_list = load_data()

# --- Sidebar ---
with st.sidebar:
    st.header("Data Context")
    st.caption(f"Input File: `{INPUT_FILE}`")
    st.write(f"**Rows:** {len(df_source)}")
    st.write("**Columns:**")
    st.code(list(df_source.columns))
    
    st.divider()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as file:
            st.download_button("📥 Download Batch Results", file, "batch_results.csv")

# --- Tabs ---
tab1, tab2 = st.tabs(["📝 Prompt Editor", "🚀 Batch Runner"])

# TAB 1: EDITOR
with tab1:
    col_list, col_edit = st.columns([1, 2])
    
    with col_list:
        st.subheader("Select Prompt")
        # Helper to select a prompt by name
        names = [p['name'] for p in prompts_list] + ["+ Create New"]
        selected_name = st.radio("Available Prompts", names)
        selected_data = next((p for p in prompts_list if p['name'] == selected_name), None)

    with col_edit:
        st.subheader("Configuration")
        with st.form("edit_form"):
            if selected_data:
                f_id = st.text_input("ID", value=selected_data['id'], disabled=True)
                f_name = st.text_input("Name", value=selected_data['name'])
                # NOTE: We removed the mutual exclusivity logic. Multiple prompts can be active.
                f_active = st.checkbox("Active for Batch (Show in Runner)", value=selected_data.get('is_active', False))
                f_template = st.text_area("Template", value=selected_data['template'], height=250)
            else:
                f_id = st.text_input("ID (Unique)", value=f"prompt_{int(time.time())}")
                f_name = st.text_input("Name", value="New Prompt")
                f_active = st.checkbox("Active for Batch (Show in Runner)", value=True)
                f_template = st.text_area("Template", placeholder="Hello {customer_name}...", height=250)

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

# TAB 2: BATCH RUNNER
with tab2:
    st.header("Execute Batch")
    
    # 1. Filter for Active Prompts
    active_candidates = [p for p in prompts_list if p.get('is_active')]
    
    if not active_candidates:
        st.warning("No prompts are marked as 'Active'. Go to the Editor and check 'Active for Batch' on the prompts you want to run.")
    else:
        st.markdown("Select which active prompts to run against the data:")
        
        # 2. Multiselect allowing user to pick from the Active ones
        # We default to ALL active prompts being selected
        candidate_names = [p['name'] for p in active_candidates]
        selected_names = st.multiselect(
            "Prompts included in this run:",
            options=candidate_names,
            default=candidate_names
        )
        
        # Filter the full objects based on name selection
        prompts_to_run = [p for p in active_candidates if p['name'] in selected_names]
        
        col_run_a, col_run_b = st.columns(2)
        with col_run_a:
            st.info(f"Input Rows: {len(df_source)}")
        with col_run_b:
            st.info(f"Prompts Selected: {len(prompts_to_run)}")
            st.caption(f"Total LLM Calls: {len(df_source) * len(prompts_to_run)}")

        # 3. Execution Trigger
        if st.button("🚀 Run Batch for Selected Prompts", type="primary", disabled=len(prompts_to_run)==0):
            with st.spinner("Running batch inference..."):
                df_result, msg = run_batch_job(df_source, prompts_to_run)
                
                if df_result is not None:
                    st.success(msg)
                    st.subheader("Preview Results (First 10 rows)")
                    # Sort by customer so we can compare prompt versions easily
                    st.dataframe(df_result.sort_values(by="customer_id").head(10), use_container_width=True)
                else:
                    st.error(msg)



