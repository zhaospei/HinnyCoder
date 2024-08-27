import json

class Tools:
    @staticmethod
    def read_code(fname):
        with open(fname, 'r', encoding='utf8') as f:
            return f.read()
    @staticmethod
    def dump_json(obj, fname):
        with open(fname, 'w', encoding='utf8') as f:
            json.dump(obj, f)

    @staticmethod
    def dump_jsonl(obj, fname):
        with open(fname, 'w', encoding='utf8') as f:
            for item in obj:
                f.write(json.dumps(item) + '\n')
    
    @staticmethod
    def load_jsonl(fname):
        with open(fname, 'r', encoding='utf8') as f:
            lines = []
            for line in f:
                lines.append(json.loads(line))
            return lines


file_path = 'raw_gen/rambo_defects4j_sketch_prompt_deepseek-coder-6.7b-base.jsonl' 

import pandas as pd

type_parquet = pd.read_parquet('type_extract/rambo_upperbound_defects4j_re.parquet', engine='fastparquet')

lines = Tools.load_jsonl(file_path)

# wrong_task_ids = open('worng_task_ids.txt', 'r').read().split('\n')
wrong_task_ids = [
    "5e41187c16e6acd79f435b1a18312ee7ed86ff3a228e95c6269e523e78c37552",
    "c65e93ae3eb54f0f0812e0231fd992503a7b113314a5e62492d6cf555487fe24",
    "cc7b53b6a234d2b7f952bc7cf38c6206f4a7910491d8a0c414ed4600f17588c1",
]


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

new_lines_json = []

for line in lines:
    new_line = line
    if line['metadata']['defects4j_task_id'] in wrong_task_ids:
        continue
    # new_line['choices'] = [clean_output(line['choices'][i]['text']) for i in range(len(line['choices']))]
    new_line['choices'] = [line['metadata']['ground_truth']]
    # print(line['metadata']['task_id'])
    
    df_type = type_parquet[type_parquet['rambo_task_id'] == line['metadata']['task_id']]
    if len(df_type) != 1:
        print('Error: ', line['metadata']['task_id'])
    # print(df_type['prediction.types']
    new_line['metadata']['method'] = df_type['ground_truth.methods'].values[0]
    new_line['metadata']['type'] = df_type['ground_truth.types'].values[0]
    new_lines_json.append(new_line)

Tools.dump_jsonl(new_lines_json, 'type_extract/defects4j_groundtruth_type_method.jsonl')