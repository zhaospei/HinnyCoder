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

file_path = 'raw_gen/rambo_grounth_truth_no_em_type_method_deepseek-coder-6.7b-base.jsonl'

print(f'generating from {file_path}')
lines = Tools.load_jsonl(file_path)
# have a new line at the end
# wrong_task_ids = open('worng_task_ids.txt', 'r').read().split('\n')
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

prompts = [f"{line['prompt']}\n" for line in lines]
task_ids = [line['metadata']['task_id'] for line in lines]
# defects4j_task_id = [line['metadata']['defects4j_task_id'] for line in lines]
fpath_tuple = ['/'.join(line['metadata']['fpath_tuple'][1:]) for line in lines]
project_name = [line['metadata']['task_id'].split('/')[0] for line in lines]
ground_truths = [line['metadata']['ground_truth'] for line in lines]
class_name  = [line['metadata']['class_name'] for line in lines]
func_name = [line['metadata']['function_name'] for line in lines]
masked_class = [line['metadata']['left_context'] + '<FILL_FUNCTION_BODY>' + line['metadata']['right_context'] for line in lines]
types  = [list(line['metadata']['type']) for line in lines]
methods = [list(line['metadata']['method']) for line in lines]
clean_samples = []

print(types)

for line in lines:
    samples = [line['choices'][i]['text'] for i in range(len(line['choices']))]
    clean_sample = clean_output(samples[0])
    clean_samples.append(clean_sample)
# print(clean_sample)

import pandas as pd

df = pd.DataFrame({
    'task_id': task_ids,
    # 'rambo_task_id': task_ids,
    'relative_path': fpath_tuple,
    'proj_name': project_name,
    'class_name': class_name,
    'func_name': func_name,
    'masked_class': masked_class,
    'prompt': prompts,
    'prediction': clean_samples,
    'ground_truth': ground_truths,
    # 'type': types,
    # 'method': methods
    })
df.to_parquet('predicts/rambo_ground_truth_output.parquet', engine='fastparquet')
