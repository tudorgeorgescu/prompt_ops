
import os
import json
import pandas as pd

# File paths
PROMPTS_FILE = 'prompts.json'
INPUT_FILE = 'source_data.csv'
SCHEMA_FILE = 'schema_config.json'

def load_data():
    df_input = pd.read_csv(INPUT_FILE) if os.path.exists(INPUT_FILE) else pd.DataFrame()
    prompts_data = []
    schema_data = {}

    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r') as f:
            prompts_data = json.load(f)

    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, 'r') as f:
            schema_data = json.load(f)

    return df_input, prompts_data, schema_data

def save_prompts(prompts_list):
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts_list, f, indent=2)
