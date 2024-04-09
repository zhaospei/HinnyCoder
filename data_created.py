import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm

df = pd.read_parquet(f'java-42k.parquet', engine='fastparquet')
model_id = 'deepseek-ai/deepseek-coder-6.7b-base'

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
input_ls = []
output_ls = []
with tqdm(total=len(df), desc="gen") as pbar:
    for _, row in df.iterrows():
        model_input = tokenizer(row['masked_contract'], return_tensors="pt").to("cuda")
        input_ls.append(model_input['input_ids'].size()[1])
        model_input = tokenizer(row['func_body'], return_tensors="pt").to("cuda")
        output_ls.append(model_input['input_ids'].size()[1])
        pbar.update(1)