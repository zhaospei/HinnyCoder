import json
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




# with open('leakable.txt', 'r') as f:
#     raw_text = f.read()
# lines = raw_text.split('----------------------------------------------------------------------------------------------------')[:-1]
# lines = [line.strip() for line in lines]
# import os

# relative_paths = []
# inner_classes = []
# outer_classes = []
# function_names = []
# for line in lines:
#     # print(len(line.split('\n')))
#     proj_name, relative_path, outer_class, inner_class, function_name = line.split('\n')
#     relative_path = proj_name + '/' + relative_path
#     relative_paths.append(relative_path)
#     inner_classes.append(inner_class)
#     outer_classes.append(outer_class)
#     function_names.append(function_name)

# for i in range(len(relative_paths)):
#     print(f'{relative_paths[i]} {inner_classes[i]} {outer_classes[i]} {function_names[i]}')

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


file_path = 'raw_gen/rambo_sketch_bamboo_deepseek-coder-6.7b-base_starcoder2-3b.jsonl' 

# import pandas as pd

# type_parquet = pd.read_parquet('type_extract/full_context_hinny_no_param_name_k20_t8000.parquet', engine='fastparquet')

lines = Tools.load_jsonl(file_path)

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

gt_list = []
prd_list = []

count = 0

# wrong_task_ids = []


for line in lines:
    ok = False
    # for path, inner_class, outer_class, function_name in zip(relative_paths, inner_classes, outer_classes, function_names):
    #     if tuple(path.split('/')) == tuple(line['metadata']['fpath_tuple']) and \
    #     inner_class == line['metadata']['class_name'] and \
    #     function_name == line['metadata']['function_name']:
    if line['metadata']['task_id'] in wrong_task_ids:
            ok = True
    count += 1
    if ok:
        # wrong_task_ids.append(line['metadata']['task_id'])
        continue
    samples = [line['choices'][i]['text'] for i in range(len(line['choices']))]
    # samples = [line['choices'][i]for i in range(len(line['choices']))]

    clean_sample = clean_output(samples[0])
    # print(clean_sample)
    # print("------------------------")
    gt = line['metadata']['ground_truth']
    gt_list.append(gt)
    prd_list.append(clean_sample)

gt_list_ = [' '.join(x.split()).strip() for x in gt_list]
prd_list_ = [' '.join(x.split()).strip() for x in prd_list]

print(len(prd_list_))

    
with open('data/500.test.hinny.return.type.gt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(gt_list_))
    
with open('data/500.test.repocoder.return.type.gen', 'w', encoding='utf-8') as f:
    f.write('\n'.join(prd_list_))

# with open('worng_task_ids.txt', 'w', encoding='utf-8') as f:
#     f.write('\n'.join(wrong_task_ids))