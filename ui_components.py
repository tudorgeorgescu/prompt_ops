import streamlit as st
from utils import safe_float

def render_parameters(session_key, param header_cols = st.columns([0.5, 0.3, 0.2])def render_parameters(session_key, param_list):
    with header_cols[0]: st.markdown("**Name**")
    with header_cols[1]: st.markdown("**Value**")
    with header_cols[2]: st.markdown("**Action**")

    if len(param_list) == 0:
        st.info("No parameters defined yet.")
    else:
        for i, p in enumerate(param_list):
            row_cols = st.columns([0.5, 0.3, 0.2])
            with row_cols[0]:
                st.text_input("Name", value=p.get("name", ""), key=f"{session_key}_name_{i}", label_visibility="collapsed")
            with row_cols[1]:
                st.number_input("Value", value=safe_float(p.get("value", 0.0)), key=f"{session_key}_val_{i}", step=1.0, label_visibility="collapsed")
            with row_cols[2]:
                st.write("")
                if st.button("🗑️ Remove", key=f"{session_key}_del_{i}"):
                    param_list.pop(i)
                    st.session_state[session_key] = param_list
                    st.rerun()

    # Sync edits
    synced = []
    for i in range(len(param_list)):
        synced.append({
            "name": st.session_state.get(f"{session_key}_name_{i}", "").strip(),
            "value": safe_float(st.session_state.get(f"{session_key}_val_{i}", 0.0))
        })
    st.session_state[session_key] = synced

    # Add new parameter
    st.divider()
    new_name = st.text_input("New parameter name", key=f"{session_key}_new_name")
    new_val = st.number_input("New parameter value", key=f"{session_key}_new_val", value=0.0, step=1.0)
    if st.button("➕ Add parameter", key=f"{session_key}_add_btn"):
        if new_name.strip():
            param_list.append({"name": new_name.strip(), "value": safe_float(new_val)})
            st.session_state[session_key] = param_list
            st.rerun()
        else:
            st.warning("Please provide a parameter name.")
    st.subheader("Insight Parameters")
    st.caption("Create numeric parameters for this insight.")

