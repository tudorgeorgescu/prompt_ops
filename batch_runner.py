import time
import streamlit as st
import pandas as pd
from datetime import datetime


def mock_llm_call(prompt_text, model_name="gpt-mock"):
    time.sleep(0.05)
    return f"[{model_name}]: Response to '{prompt_text[:15]}...'"

def run_batch_job(df_input, selected_prompts_list, output_file='batch_results.csv'):
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
    df_results.to_csv(output_file, index=False)
    return df_results, f"Success! Generated {len(df_results)} outputs."


