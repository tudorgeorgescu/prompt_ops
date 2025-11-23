
import streamlit as st
import re
import time
from datetime import datetime
from data_manager import load_data, save_prompts
from utils import normalize_params
from ui_components import render_parameters
from batch_runner import run_batch_job

OUTPUT_FILE = 'batch_results.csv'

st.set_page_config(layout="wide", page_title="Cloud Prompt Ops")
st.title("⚡ Cloud Prompt A/B Tester")

df_source, prompts_list, schema_dict = load_data()

tab1, tab2 = st.tabs(["🧠 Insight Editor", "🚀 Batch Runner"])

with tab1:
    st.subheader("Select Insight")
    options = [p['name'] for p in prompts_list] + ["+ Create New"]
    selected_name = st.segmented_control("Insights", options, label_visibility="collapsed")
    selected_data = next((p for p in prompts_list if p['name'] == selected_name), None)
    current_id = selected_data['id'] if selected_data else "__new__"
    session_key = f"param_list_{current_id}"

    if session_key not in st.session_state:
        st.session_state[session_key] = normalize_params(selected_data.get("params", [])) if selected_data else []

    param_list = st.session_state[session_key]
    render_parameters(session_key, param_list)

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

        if st.form_submit_button("Save Insight"):
            new_entry = {
                "id": f_id,
                "name": f_name,
                "template": f_template,
                "is_active": f_active,
                "params": st.session_state[session_key],
                "updated_at": datetime.now().isoformat()
            }
            if selected_data:
                prompts_list[prompts_list.index(selected_data)] = new_entry
            else:
                prompts_list.append(new_entry)
            save_prompts(prompts_list)
            st.success("Saved!")
            st.rerun()

with tab2:
    st.header("Execute Batch")
    active_candidates = [p for p in prompts_list if p.get('is_active')]
    if not active_candidates:
        st.warning("No active prompts found.")
    else:
        candidate_names = [p['name'] for p in active_candidates]
        selected_names = st.multiselect("Active Prompts", candidate_names, default=candidate_names)
        prompts_to_run = [p for p in active_candidates if p['name'] in selected_names]
        if st.button("🚀 Run Batch", type="primary", disabled=not prompts_to_run):
            with st.spinner("Running..."):
                df_result, msg = run_batch_job(df_source, prompts_to_run, OUTPUT_FILE)
                if df_result is not None:
                    st.success(msg)
                    st.dataframe(df_result.head(10), use_container_width=True)
                else:
                    st.error(msg)
