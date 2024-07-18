import pandas as pd
from transformers import AutoTokenizer
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
 
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Counting length"):
        model_input = tokenizer(row['masked_class'], return_tensors="pt")
        input_ls.append(model_input['input_ids'].size()[1])
        model_input = tokenizer(row['func_body'], return_tensors="pt")
        output_ls.append(model_input['input_ids'].size()[1])

    df['len_input'] = input_ls
    df['len_output'] = output_ls

    df['total'] = df['len_input'] + df['len_output']

    df = df[df['total'] <= 2048]

    return df