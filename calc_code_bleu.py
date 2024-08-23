from codebleu import calc_codebleu

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

wrong_task_ids = [
    "5e41187c16e6acd79f435b1a18312ee7ed86ff3a228e95c6269e523e78c37552",
    "c65e93ae3eb54f0f0812e0231fd992503a7b113314a5e62492d6cf555487fe24",
    "cc7b53b6a234d2b7f952bc7cf38c6206f4a7910491d8a0c414ed4600f17588c1",
    "37497bed336eb012890fc7770295b46f192ccf65b0f828d783eedd1a47cdafb5",
    "cc8f907557109ee35b048274c78d08e61cfb8579560cb8b9aef4fd0503453e42",
    "cca1fe2017686735e48e23576404d10dde66cfc5926280308f0f99fab1377f0c",
    "fae7ab2c7d32932ef3e7c0aea28f376b843bb53fe6dbcd8bf8f2f8ac2657c051",
]

wrong_task_ids = open('worng_task_ids.txt', 'r').read().split('\n')

file_path = 'raw_gen/rambo_sketch_bamboo_deepseek-coder-6.7b-base_starcoder2-3b.jsonl'

print(f'generating from {file_path}')
lines = Tools.load_jsonl(file_path)
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

ground_truths  = []
for line in lines:
    if line['metadata']['task_id'] in wrong_task_ids:
        continue
    ground_truths.append(line['metadata']['ground_truth'])

print(len(ground_truths))

predictions = []

for line in lines:
    if line['metadata']['task_id'] in wrong_task_ids:
        continue
    samples = [line['choices'][i]['text'] for i in range(len(line['choices']))]
    clean_sample = clean_output(samples[0])
    predictions.append(clean_sample)
    
scores = []

for pred, gt in zip(predictions, ground_truths):
    res = calc_codebleu([gt], [pred], lang="java")
    scores.append(res['codebleu'])

avg_scores = round(sum(scores) / len(scores) * 100, 2)
print(len(scores))
print(f'Average CodeBLEU: {avg_scores}')
