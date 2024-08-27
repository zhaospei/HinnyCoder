import json

class Tools:
    @staticmethod
    def load_jsonl(path):
        with open(path, 'r') as f:
            return [json.loads(line) for line in f.readlines()]

    @staticmethod
    def dump_jsonl(obj, path):
        with open(path, 'w') as f:
            for line in obj:
                f.write(json.dumps(line) + '\n')

file_path = 'raw_gen/defects4j_grounth_truth_no_em_type_method_cutting_deepseek-coder-6.7b-base.jsonl'

print(f'generating from {file_path}')
line_32s = Tools.load_jsonl(file_path)
# repocoder_lines = Tools.load_jsonl('raw_gen/hinnycoder-s1-one-gram-ws-20-ss-2_deepseek-coder-6.7b-base.jsonl')
line_36s = Tools.load_jsonl('raw_gen/defects4j_grounth_truth_no_em_type_method_deepseek-coder-6.7b-base.jsonl')
line_39s = Tools.load_jsonl('raw_gen/defects4j-rg-one-gram-ws-20-ss-2-fix-fpath_8000_deepseek-coder-6.7b-base.jsonl')
# have a new line at the end
def clean_output(output):
    cur_bracket = 0
    for idx, c in enumerate(output):
        if c == '{':
            cur_bracket += 1
        elif c == '}':
            cur_bracket -= 1
        
        # print(c, ' ', cur_bracket)
        
        if cur_bracket < 0:
            return output[:idx]
    
    return output

prompts = [f"{line['prompt']}\n" for line in line_32s]
task_ids = [line['metadata']['task_id'] for line in line_32s]
fpath_tuple = ['/'.join(line['metadata']['fpath_tuple'][1:]) for line in line_32s]
project_name = [line['metadata']['task_id'].split('/')[0] for line in line_32s]
ground_truths = [line['metadata']['ground_truth'] for line in line_32s]
class_name  = [line['metadata']['class_name'] for line in line_32s]
func_name = [line['metadata']['function_name'] for line in line_32s]
masked_class = [line['metadata']['left_context'] + '<FILL_FUNCTION_BODY>' + line['metadata']['right_context'] for line in line_32s]
clean_samples = []

for line in line_32s:
    samples = [line['choices'][i]['text'] for i in range(len(line['choices']))]
    clean_sample = clean_output(samples[0])
    clean_samples.append(clean_sample)
# print(clean_sample)

line_36_prompts = []
line_36_clean_samples = []

for idx in task_ids:
    for line in line_36s:
        if line['metadata']['task_id'] == idx:
            line_36_prompts.append(line['prompt'])
            line_36_clean_samples.append(clean_output(line['choices'][0]['text']))
            break

line_39_prompts = []
line_39_clean_samples = []

for idx in task_ids:
    for line in line_39s:
        if line['metadata']['task_id'] == idx:
            line_39_prompts.append(line['prompt'])
            line_39_clean_samples.append(clean_output(line['choices'][0]['text']))
            break
            

import pandas as pd

df = pd.DataFrame({
    'task_id': task_ids,
    'relative_path': fpath_tuple,
    'proj_name': project_name,
    'class_name': class_name,
    'func_name': func_name,
    'masked_class': masked_class,
    'rambo_cutting_prompt': prompts,
    'rambo_cutting_prediction': clean_samples,
    'rambo_prompt': line_36_prompts,
    'rambo_prediction': line_36_clean_samples,
    'repocoder_prompt': line_39_prompts,
    'repocoder_prediction': line_39_clean_samples,
    'ground_truth': ground_truths
    })

df.to_parquet('prompts/rambo_rambocutting_repocoder_no_em_compare.parquet', engine='fastparquet')
