raw = open('len_elements.txt', 'r').readlines()

raw = [int(r.split('\n')[0]) for r in raw]

temp = []

for r in raw:
    if r > 1:
        temp.append(r)

print(len(temp))

dict = {'len': temp}

import pandas as pd

df = pd.DataFrame(dict)

cc = []

for r in temp:
    if r < 500:
        cc.append(r)

print(len(cc) / len(temp))

cc2 = []

for r in temp:
    if r < 1024:
        cc2.append(r)

print(len(cc) / len(temp))

print(len(cc2) / len(temp))


print(df['len'].describe())