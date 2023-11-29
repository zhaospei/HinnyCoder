import pandas as pd

def get_id(dir_path='cmg-data/split-data', type='randomly'):
    with open(f'{dir_path}/{type}/train_id.txt') as file:
        train_id = [line.rstrip() for line in file]
    with open(f'{dir_path}/{type}/test_id.txt') as file:
        test_id = [line.rstrip() for line in file]
    return train_id, test_id

df = pd.read_parquet(f'cmg-data/cmg-data-processed.parquet', engine='fastparquet')
# df = df['text'].to_list()
# print(df[0])
train_id, test_id = get_id(dir_path='cmg-data/split-data', type='cross_project')
train, test = df.loc[df['index'].isin(train_id)], df.loc[df['index'].isin(test_id)]

import json

map_cms = json.loads(open('map_index_message.json').read())
result = list()
map_idx = dict()
idx = 0
with open('fixing_vcc.1698051913') as f:
    for l in f.readlines():
        data  = json.loads(l.strip())
        rp = data['repo_name']
        fx = rp+'_'+data['fixing_commit']['commit_hash']
        vccs = list()
        for vcc in data['vulnerability_contributing_commits']:
            vcc = rp+'_'+vcc['commit_hash']
            if vcc in map_cms.keys():
                vccs.append(map_cms[vcc])
        if len(vccs) <= 0:
            continue
        map_idx[fx] = idx
        result.append({'commit_id':fx,'message':map_cms[fx],'vccs_message':'\n'.join(vccs)})
        idx += 1
print(len(result))

import nltk
from nltk import WordNetLemmatizer, pos_tag, WordPunctTokenizer, data
from nltk.corpus import wordnet
from tqdm import tqdm
import re

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'w') as fout:
        fout.write(string)

def word_tokenizer(sentence):
    words = WordPunctTokenizer().tokenize(sentence)
    return words

examples = []

indexs = train['index'].unique()

for index in tqdm(indexs):
    df_commit = train[train['index']==index]
    source_seq = ''
    vcc_msgs = ''
    for _, row in df_commit.iterrows():
        if row['old_path_file'] != None:
            source_seq += '--- ' + row['old_path_file'] + '\n'
        if row['new_path_file'] != None:
            source_seq += '+++ ' + row['new_path_file'] + '\n'
        source_seq += row['diff'] + '\n'
        
        label_words = row['label'].split()
        target_seq = ' '.join(label_words)
        
    if index in map_idx.keys():
        res = result[map_idx[index]]
        vcc_msgs = res['vccs_message']
    examples.append({'diff': source_seq, 'msg': target_seq, 'vccs_msg': vcc_msgs})

import json
def dump_to_file(obj, file):
    with open(file,'w+') as f:
        for el in obj:
            f.write(json.dumps(el)+'\n')
            
dump_to_file(examples,'train.jsonl')

import nltk
from nltk import WordNetLemmatizer, pos_tag, WordPunctTokenizer, data
from nltk.corpus import wordnet
from tqdm import tqdm
import re

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'w') as fout:
        fout.write(string)

def word_tokenizer(sentence):
    words = WordPunctTokenizer().tokenize(sentence)
    return words

examples = []

indexs = test['index'].unique()

for index in tqdm(indexs):
    df_commit = test[test['index']==index]
    source_seq = ''
    vcc_msgs = ''
    for _, row in df_commit.iterrows():
        if row['old_path_file'] != None:
            source_seq += '--- ' + row['old_path_file'] + '\n'
        if row['new_path_file'] != None:
            source_seq += '+++ ' + row['new_path_file'] + '\n'
        source_seq += row['diff'] + '\n'
        
        label_words = row['label'].split()
        target_seq = ' '.join(label_words)
        
    if index in map_idx.keys():
        res = result[map_idx[index]]
        vcc_msgs = res['vccs_message']
                
    prompt = f"Give a short commit message for code from:\n- History commit messages:\n{{vccs}}\n- Git diff:\n{{diff}}\n---\nShort commit message:\n".format(vccs=vcc_msgs, diff=source_seq)
    examples.append({'prompt': prompt})

import json
def dump_to_file(obj, file):
    with open(file,'w+') as f:
        for el in obj:
            f.write(json.dumps(el)+'\n')
dump_to_file(examples,'test.input.jsonl')  
    # write_string_to_file("test.input", prompt + "<nl>")