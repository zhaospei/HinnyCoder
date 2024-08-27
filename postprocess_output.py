import pandas as pd

df = pd.read_parquet('data/180724_500_similar_method_retrieved_context.parquet', engine='fastparquet')

raw_outputs = open('raw_gen/500_gen_ground_truth_first.output', 'r', encoding="utf-8").read().split('<nl>')[:-1]

def clean_output(output):
    cur_bracket = 0
    for idx, c in enumerate(output):
        if c == '{':
            cur_bracket += 1
        elif c == '}':
            cur_bracket -= 1
        
        if cur_bracket < 0:
            return output[:idx]
    
    return output

clean_output = [clean_output(output) for output in raw_outputs]

df['similar_method_output'] = clean_output
df.to_parquet('data/180724_500_similar_method_retrieved_context_ground_truth_first.parquet', engine='fastparquet')

gen_txt_tk = [' '.join(x.split()).strip() for x in clean_output]


with open('data/190724.500.gen_ground_truth_first', 'w') as f:
    f.write('\n'.join(gen_txt_tk))