import pandas as pd
import numpy as np

df = pd.read_parquet(f'masked_all_func_body_v1.parquet', engine='fastparquet')

from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = 'deepseek-ai/deepseek-coder-6.7b-base'

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )

from tqdm import tqdm

input_ls = []
output_ls = []
with tqdm(total=len(df), desc="gen") as pbar:
    for _, row in df.iterrows():
        model_input = tokenizer(row['masked_contract'], return_tensors="pt").to("cuda")
        input_ls.append(model_input['input_ids'].size()[1])
        model_input = tokenizer(row['func_body'], return_tensors="pt").to("cuda")
        output_ls.append(model_input['input_ids'].size()[1])
        pbar.update(1)

df['len_input'] = input_ls
df['len_output'] = output_ls

df['total'] = df['len_input'] + df['len_output']

df = df[df['total'] <= 2048]

df.to_parquet(f'data-50k.parquet', engine='fastparquet')

