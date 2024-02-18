import datasets
from tqdm import tqdm

raw = datasets.load_dataset('lvdthieu/compile_error_and_inherit_element', split='validation')

from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = 'deepseek-ai/deepseek-coder-6.7b-base'

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )

input_ls = []
# output_ls = []
with tqdm(total=len(raw), desc="gen") as pbar:
    for row in raw:
        model_input = tokenizer(row['compile_info'], return_tensors="pt").to("cuda")
        input_ls.append(str(model_input['input_ids'].size()[1]))
        # model_input = tokenizer(row['func_body'], return_tensors="pt").to("cuda")
        # output_ls.append(model_input['input_ids'].size()[1])
        pbar.update(1)

with open('len.txt', 'w') as f:
    f.write('\n'.join(input_ls))