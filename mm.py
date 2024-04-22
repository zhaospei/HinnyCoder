import datasets
from tqdm import tqdm
import pandas as pd

raw = datasets.load_dataset('lvdthieu/java-48k-relevant-context', split='validation')
# raw = pd.read_parquet(f'test_refine+.parquet', engine='fastparquet')

from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = 'deepseek-ai/deepseek-coder-6.7b-base'

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
input_ls = []
# output_ls = []
temp = []


with tqdm(total=len(raw), desc="gen") as pbar:
    for row in raw:
        model_input = tokenizer(row['inherit_elements'], return_tensors="pt").to("cuda")
        input_ls.append(str(model_input['input_ids'].size()[1]))    
        # model_input = tokenizer(row['func_body'], return_tensors="pt").to("cuda")
        # output_ls.append(model_input['input_ids'].size()[1])
        pbar.update(1)

with open('len_elements.txt', 'w') as f:
    f.write('\n'.join(input_ls))

# import json
# def dump_to_file(obj, file):
#     with open(file,'w+') as f:
#         for el in obj:
#             f.write(json.dumps(el)+'\n')
            
# dump_to_file(temp,'test.jsonl')

# from huggingface_hub import HfApi
# api = HfApi()

# # api.create_repo('zhaospei/all_you_want')

# api.upload_file(
#     path_or_fileobj="test.jsonl",
#     path_in_repo="test.jsonl",
#     repo_id="zhaospei/data-50k-test-final-gen2",
#     repo_type="dataset",
# )