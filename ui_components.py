
import streamlit as st
from utils import safe_float, normalize_params

def render_parameters(session_key, param_list):
    """
    Render a parameter editor:
    - param_list must be a list of dicts [{name:str, value:float}]
    - This function will coerce bad inputs using normalize_params()
    """
    # Defensive: coerce bad inputs
    if not isinstance(param_list, list):
        param_list = normalize_params(param_list)
        st.session_state[session_key] = param_list

    st.subheader("Insight Parameters")
    parameter_container = st.container(border=True)
    parameter_container.caption("Create numeric parameters for this insight.")

    header_cols = parameter_container.columns([0.5, 0.3, 0.2])
    with header_cols[0]:
        parameter_container.markdown("**Name**")
    with header_cols[1]:
        parameter_container.markdown("**Value**")
    with header_cols[2]:
        parameter_container.markdown("**Action**")

    if len(param_list) == 0:
        parameter_container.info("No parameters defined yet.")
    else:
        for i, p in enumerate(param_list):
            # Final defensive defaults
            name_val = "" if not isinstance(p, dict) else str(p.get("name", ""))
            num_val = 0.0 if not isinstance(p, dict) else safe_float(p.get("value", 0.0), 0.0)

            row_cols = parameter_container.columns([0.5, 0.3, 0.2])
            with row_cols[0]:
                parameter_container.text_input(
                    "Name",
                    value=name_val,
                    key=f"{session_key}_name_{i}",
                    label_visibility="collapsed"
                )
            with row_cols[1]:
                parameter_container.number_input(
                    "Value",
                    value=num_val,
                    key=f"{session_key}_val_{i}",
                    step=1.0,
                    label_visibility="collapsed"
                )
            with row_cols[2]:
                # Spacer to align the button roughly with inputs
                parameter_container.write("")
                if parameter_container.button("🗑️ Remove", key=f"{session_key}_del_{i}"):
                    updated = list(param_list)
                    if i < len(updated):
                        updated.pop(i)
                    parameter_container.session_state[session_key] = updated
                    parameter_container.rerun()

    # Sync edits back to session
    synced = []
    for i in range(len(param_list)):
        synced.append({
            "name": (parameter_container.session_state.get(f"{session_key}_name_{i}", "") or "").strip(),
            "value": safe_float(parameter_container.session_state.get(f"{session_key}_val_{i}", 0.0), 0.0)
        })
    parameter_container.session_state[session_key] = synced

    # Add new parameter
    st.divider()
    new_name = st.text_input("New parameter name", key=f"{session_key}_new_name", placeholder="e.g., threshold")
    new_val = st.number_input("New parameter value", key=f"{session_key}_new_val", value=0.0, step=1.0)
    if st.button("➕ Add parameter", key=f"{session_key}_add_btn"):
        if new_name.strip():
            current = list(st.session_state.get(session_key, []))
            current.append({"name": new_name.strip(), "value": safe_float(new_val, 0.0)})
            st.session_state[session_key] = current
            # Clear inputs after add
            st.session_state[f"{session_key}_new_name"] = ""
            st.session_state[f"{session_key}_new_val"] = 0.0
            st.rerun()
        else:
            st.warning("Please provide a parameter name.")
