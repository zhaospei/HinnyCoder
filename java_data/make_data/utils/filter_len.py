import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm

model_id = "deepseek-ai/deepseek-coder-6.7b-base"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

def count_token(df: pd.DataFrame) -> pd.DataFrame:
    """Count and set limit number of tokens for samples 

    Args:
        df (pd.DataFrame): Input dataset

    Returns:
        pd.DataFrame: Output dataset, after filtered long samples
    """
    input_ls = []
    output_ls = []
    with tqdm(total=len(df), desc="Counting length") as pbar:
        for _, row in df.iterrows():
            model_input = tokenizer(row['masked_class'], return_tensors="pt").to("cuda")
            input_ls.append(model_input['input_ids'].size()[1])
            model_input = tokenizer(row['func_body'], return_tensors="pt").to("cuda")
            output_ls.append(model_input['input_ids'].size()[1])
            pbar.update(1)

    df['len_input'] = input_ls
    df['len_output'] = output_ls

    df['total'] = df['len_input'] + df['len_output']

    df = df[df['total'] <= 2048]

    return df