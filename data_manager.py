import os
import json
import pandas as pd

PROMPTS_FILE = 'prompts.json'
INPUT.read_csv(INPUT_FILE) if os.path.exists(INPUT_FILE) else pd.DataFrame()INPUT_FILE = 'source_data.csv'
    prompts_data = json.load(open(PROMPTS_FILE)) if os.path.exists(PROMPTS_FILE) else []
    schema_data = json.load(open(SCHEMA_FILE)) if os.path.exists(SCHEMA_FILE) else {}
    return df_input, prompts_data, schema_data

def save_prompts(prompts_list):
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts_list, f, indent=2)
SCHEMA_FILE = 'schema_config.json'

def load_data():
