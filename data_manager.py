
import os
import json
import pandas as pd

PROM load_data():PROMPTS_FILE = 'prompts.json'
    df_input = pd.read_csv(INPUT_FILE) if os.path.exists(INPUT_FILE) else pd.DataFrame()
    prompts_data = json.load(open(PROMPTS_FILE)) if os.path.exists(PROMPTS_FILE) else []
    schema_data = json.load(open(SCHEMA_FILE)) if os.path.exists(SCHEMA_FILE) else {}
    return df_input, prompts_data, schema_data

def save_prompts(prompts_list):
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts_list, f, indent=2)
INPUT_FILE = 'source_data.csv'
SCHEMA_FILE = 'schema_config.json'

