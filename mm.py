import datasets
from tqdm import tqdm

raw = datasets.load_dataset('zhaospei/all_you_want', split='validation')

from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = 'deepseek-ai/deepseek-coder-6.7b-base'

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
input_ls = []
# output_ls = []
temp = []


with tqdm(total=len(raw), desc="gen") as pbar:
    for row in raw:
        # print(type(row['inherit_elements']))
        # cc = 
        # ll = row['inherit_elements'][1:-1]
        # ll = ll.split("', '")
        # ll[0] = ll[0][1:]
        # ll[-1] = ll[-1][:-1]
        # ll = [l.replace('\n', ' ') for l in ll]
        # ll = [l.replace('<BODY>', '') for l in ll]
        # # ll = '<'
        # ll = '\n'.join(ll)
        # # print(ll)
        # temp.append({
        #     'file_source_idx': row['file_source_idx'],
        #     'contract_name': row['contract_name'],
        #     'func_name': row['func_name'],
        #     'masked_contract': row['masked_contract'],
        #     'func_body': row['func_body'],
        #     'func_body_removed_comment': row['func_body_removed_comment'],
        #     # 'len_input': row['len_input'],
        #     # 'len_output': row['len_output'],
        #     # 'total': row['total'],
        #     'deepseek_output': row['deepseek_output'],
        #     'compile_info': row['compile_info'],
        #     'inherit_elements': ll
        #     # 'deepseek': c,
        #     # 'codellama_output': row['codellama_ouput'],
        # })
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
            
# dump_to_file(temp,'valid.jsonl')

# from huggingface_hub import HfApi
# api = HfApi()

# # api.create_repo('zhaospei/all_you_want')

# api.upload_file(
#     path_or_fileobj="valid.jsonl",
#     path_in_repo="valid.jsonl",
#     repo_id="zhaospei/all_you_want",
#     repo_type="dataset",
# )