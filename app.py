
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
tab1, tab2 = st.tabs(["🧠 Insight Editor", "🚀 Batch Runner"])

# --- TAB 1: INSIGHT EDITOR ---
with tab1:
    st.subheader("Select Insight")
    options = [p['name'] for p in prompts_list] + ["+ Create New"]
    
    # Using segmented control (requires Streamlit 1.31+)
    selected_name = st.segmented_control(
        "Insights", 
        options, 
        label_visibility="collapsed"
    )
    
    selected_data = next((p for p in prompts_list if p['name'] == selected_name), None)

    
# -------------------------------
# Insight Parameters (Dynamic UI)
# -------------------------------
# Stable session key resolution even when creating a new insight
if selected_data:
    session_key = f"param_list_{selected_data.get('id', 'unknown')}"
else:
    session_key = "param_list_new_insight"

# Initialize session state safely
if session_key not in st.session_state:
    # If editing an existing insight, load its params; otherwise use empty list
    existing_params = []
    if selected_data and isinstance(selected_data.get("params", []), list):
        existing_params = selected_data.get("params", [])
    st.session_state[session_key] = existing_params

param_list = st.session_state[session_key]
# Ensure it's always a list
if not isinstance(param_list, list):
    param_list = []
    st.session_state[session_key] = []

st.subheader("Insight Parameters")
st.caption(
    "Create numeric parameters for this insight. These are stored with the insight and can be used in your logic later."
)

# Optional header row to mimic a table layout
header_cols = st.columns([0.5, 0.3, 0.2])
with header_cols[0]:
    st.markdown("**Name**")
with header_cols[1]:
    st.markdown("**Value**")
with header_cols[2]:
    st.markdown("**Action**")

# Render existing parameters with editable fields (safe when empty)
if len(param_list) == 0:
    # No parameters yet — show gentle empty state but do NOT error
    st.info("No parameters defined yet. Use the section below to add one.")
else:
    # Use a stable index range so we can safely pop during iteration via rerun
    for i in range(len(param_list)):
        p = param_list[i]
        row_cols = st.columns([0.5, 0.3, 0.2])
        with row_cols[0]:
            st.text_input(
                "Name",
                value=p.get("name", ""),
                key=f"{session_key}_name_{i}",
                placeholder="e.g., threshold",
                label_visibility="collapsed",
            )
        with row_cols[1]:
            st.number_input(
                "Value",
                value=float(p.get("value", 0.0)) if str(p.get("value", "")).strip() != "" else 0.0,
                key=f"{session_key}_val_{i}",
                step=1.0,
                label_visibility="collapsed",
            )
        with row_cols[2]:
            # Add a small spacer so the button visually aligns with inputs across themes
            st.write("")  # keeps alignment consistent without relying on vertical_alignment
            if st.button("🗑️ Remove", key=f"{session_key}_del_{i}"):
                # Remove and re-sync session state
                updated = list(st.session_state[session_key])
                if i < len(updated):
                    updated.pop(i)
                st.session_state[session_key] = updated
                st.rerun()

    # Sync edited values back to param_list
    synced = []
    for i in range(len(param_list)):
        synced.append({
            "name": st.session_state.get(f"{session_key}_name_{i}", "").strip(),
            "value": float(st.session_state.get(f"{session_key}_val_{i}", 0.0)),
        })
    st.session_state[session_key] = synced
    param_list = synced  # local reference

st.divider()

# Add new parameter controls (always visible)
new_name = st.text_input(
    "New parameter name",
    key=f"{session_key}_new_name",
    placeholder="e.g., weight_kpi",
)
new_val = st.number_input(
    "New parameter value",
    key=f"{session_key}_new_val",
    value=0.0,
    step=1.0,
)

add_cols = st.columns([0.2, 0.8])
with add_cols[0]:
    if st.button("➕ Add parameter", key=f"{session_key}_add_btn"):
        if new_name.strip():
            current = list(st.session_state[session_key])  # copy
            current.append({"name": new_name.strip(), "value": float(new_val)})
            st.session_state[session_key] = current
            # Clear input fields after add
            st.session_state[f"{session_key}_new_name"] = ""
            st.session_state[f"{session_key}_new_val"] = 0.0
            st.rerun()
        else:
            st.warning("Please provide a parameter name.")
with add_cols[1]:
    st.caption("Tip: Choose concise names. You can add as many parameters as needed.")


    # -------------------------------
    # Edit Configuration (kept intact)
    # -------------------------------
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

        if st.form_submit_button("Save Insight"):
            # Pull current params from session state
            current_params = st.session_state.get(session_key, [])
            # Filter out empty names
            current_params = [
                {"name": p.get("name", "").strip(), "value": float(p.get("value", 0.0))}
                for p in current_params if p.get("name", "").strip()
            ]

            new_entry = {
                "id": f_id,
                "name": f_name,
                "template": f_template,
                "is_active": f_active,
                "params": current_params,  # <-- NEW: persist parameters per insight
                "updated_at": datetime.now().isoformat()
            }

            if selected_data:
                prompts_list[prompts_list.index(selected_data)] = new_entry
            else:
                prompts_list.append(new_entry)
                # Rebind session key for this newly saved insight (optional)
                st.session_state[f"param_list_{f_id}"] = current_params
                # Clean up the temporary "new insight" list
                if "param_list_new_insight" in st.session_state:
                    del st.session_state["param_list_new_insight"]
            
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
