import re
import json
from tqdm import tqdm

def get_cmg_from_output(filename, tempfile):
    outl = open(filename, 'r').read().split('<nl>')
    with open(tempfile) as f:
        temp = json.load(f)
    print(len(outl))
    
    if 'response_split' not in temp:
        print('Do not have response_split feild in temp file')
        return
    
    f = open(temp['response_split'], 'w')

    for idx, line in tqdm(enumerate(outl)):
        #set idx for debug time
        if idx > 100000: 
            continue
        line = line.strip()
        try:
            line = line.split('Short commit message:')[1]
        except:
            print(line)
            line = ""
        line = line.strip()
        f.write(line + '\n')