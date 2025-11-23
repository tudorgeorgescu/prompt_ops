
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import# --- Helpers ---import re
def safe_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def normalize_params(sd_params):
    """Ensure params are a list of dicts with name:str and value:float"""
    out = []
    if isinstance(sd_params, list):
        for p in sd_params:
            if isinstance(p, dict):
                name = str(p.get("name", "")).strip()
                value = safe_float(p.get("value", 0.0), 0.0)
                out.append({"name": name, "value": value})
    return out

# --- Data Management ---
def load_data():
    if os.path.exists(INPUT_FILE):
        df_input = pd.read_csv(INPUT_FILE)
    else:
        df_input = pd.DataFrame()

    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            prompts_data = json.load(f)
    else:
        prompts_data = []

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

# --- Batch Logic ---
def run_batch_job(df_input, selected_prompts_list):
    results = []
    total_ops = max(1, len(df_input) * len(selected_prompts_list))
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

# --- UI Setup ---
st.set_page_config(layout="wide", page_title="Cloud Prompt Ops")
st.title("⚡ Cloud Prompt A/B Tester")

df_source, prompts_list, schema_dict = load_data()

# Sidebar
with st.sidebar:
    st.header("Project Context")
    st.info(f"Loaded {len(df_source)} rows from `{INPUT_FILE}`")
    
    st.divider()
    with st.expander("📚 Available Data Parameters", expanded=False):
        st.markdown("Use these variables in your template:")
        cols = df_source.columns.tolist()
        doc_data = [{"Variable": f"{{{c}}}", "Description": schema_dict.get(c, "-")} for c in cols]
        st.dataframe(pd.DataFrame(doc_data), use_container_width=True, hide_index=True)

    st.divider()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as file:
            st.download_button("📥 Download Results", file, "batch_results.csv")

# Tabs
tab1, tab2 = st.tabs(["🧠 Insight Editor", "🚀 Batch Runner"])

# --- TAB 1: INSIGHT EDITOR ---
with tab1:
    st.subheader("Select Insight")
    options = [p['name'] for p in prompts_list] + ["+ Create New"]
    selected_name = st.segmented_control("Insights", options, label_visibility="collapsed")
    selected_data = next((p for p in prompts_list if p['name'] == selected_name), None)
    current_insight_id = selected_data['id'] if selected_data else "__new__"

    # Detect selection changes and rehydrate params
    if "__current_insight_id" not in st.session_state:
        st.session_state["__current_insight_id"] = current_insight_id

    if st.session_state["__current_insight_id"] != current_insight_id:
        st.session_state["__current_insight_id"] = current_insight_id
        new_key = f"param_list_{current_insight_id}" if selected_data else "param_list_new_insight"
        st.session_state[new_key] = normalize_params(selected_data.get("params", [])) if selected_data else []

    session_key = f"param_list_{current_insight_id}" if selected_data else "param_list_new_insight"
    if session_key not in st.session_state:
        st.session_state[session_key] = normalize_params(selected_data.get("params", [])) if selected_data else []

    param_list = st.session_state.get(session_key, [])

    # Insight Parameters UI
    st.subheader("Insight Parameters")
    st.caption("Create numeric parameters for this insight. They are saved with the insight and can be used later.")

    header_cols = st.columns([0.5, 0.3, 0.2])
    with header_cols[0]: st.markdown("**Name**")
    with header_cols[1]: st.markdown("**Value**")
    with header_cols[2]: st.markdown("**Action**")

    if len(param_list) == 0:
        st.info("No parameters defined yet. Use the section below to add one.")
    else:
        for i in range(len(param_list)):
            p = param_list[i]
            row_cols = st.columns([0.5, 0.3, 0.2])
            with row_cols[0]:
                st.text_input("Name", value=p.get("name", ""), key=f"{session_key}_name_{i}", label_visibility="collapsed")
            with row_cols[1]:
                st.number_input("Value", value=safe_float(p.get("value", 0.0)), key=f"{session_key}_val_{i}", step=1.0, label_visibility="collapsed")
            with row_cols[2]:
                st.write("")  # spacer for alignment
                if st.button("🗑️ Remove", key=f"{session_key}_del_{i}"):
                    updated = list(st.session_state[session_key])
                    if i < len(updated): updated.pop(i)
                    st.session_state[session_key] = updated
                    st.rerun()

        # Sync edited values
        synced = []
        for i in range(len(param_list)):
            synced.append({
                "name": st.session_state.get(f"{session_key}_name_{i}", "").strip(),
                "value": safe_float(st.session_state.get(f"{session_key}_val_{i}", 0.0)),
            })
        st.session_state[session_key] = synced
        param_list = synced

    st.divider()
    new_name = st.text_input("New parameter name", key=f"{session_key}_new_name", placeholder="e.g., threshold")
    new_val = st.number_input("New parameter value", key=f"{session_key}_new_val", value=0.0, step=1.0)
    if st.button("➕ Add parameter", key=f"{session_key}_add_btn"):
        if new_name.strip():
            current = list(st.session_state[session_key])
            current.append({"name": new_name.strip(), "value": safe_float(new_val)})
            st.session_state[session_key] = current
            st.session_state[f"{session_key}_new_name"] = ""
            st.session_state[f"{session_key}_new_val"] = 0.0
            st.rerun()
        else:
            st.warning("Please provide a parameter name.")

    # Edit Configuration
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
            current_params = st.session_state.get(session_key, [])
            current_params = [
                {"name": p.get("name", "").strip(), "value": safe_float(p.get("value", 0.0))}
                for p in current_params if p.get("name", "").strip()
            ]
            new_entry = {
                "id": f_id,
                "name": f_name,
                "template": f_template,
                "is_active": f_active,
                "params": current_params,
                "updated_at": datetime.now().isoformat()
            }
            if selected_data:
                prompts_list[prompts_list.index(selected_data)] = new_entry
            else:
                prompts_list.append(new_entry)
                st.session_state[f"param_list_{f_id}"] = current_params
                if "param_list_new_insight" in st.session_state:
                    del st.session_state["param_list_new_insight"]
                st.session_state["__current_insight_id"] = f_id

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


# --- Configuration ---
PROMPTS_FILE = 'prompts.json'
INPUT_FILE = 'source_data.csv'
SCHEMA_FILE = 'schema_config.json'
OUTPUT_FILE = 'batch_results.csv'

