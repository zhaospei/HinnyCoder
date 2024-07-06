# merge parquets
import pandas as pd
import numpy as np

def verify(df, l = 0, r = 99999999999999999):
    l = max(0, l)
    l = min(l, len(df) - 1)
    r = max(0, r)
    r = min(r, len(df))

    print(l, r)

    all_res = []
    corrupted = []
    empt = []
    for i in range(l, r):
        row = df.iloc[i]

        if (row['relevant_context'] == None):
            corrupted.append(i)
        else:
            if (len(row['relevant_context']) == 0):
                empt.append(i)

            all_res.append(len(row['relevant_context'].split()))

    all_res.sort()

    df_l = pd.DataFrame(all_res)

    print(df_l.describe())

    print()
    print(f'corrupted cnt: {len(corrupted)}')
    print(f'corrupted: {corrupted}')

    print()
    print(f'empty cnt: {len(empt)}')
    print(f'empty: {empt}')

    return all_res

data_prefix = 'data'
raw_prefix = f'{data_prefix}/raw'
db_prefix = f'{data_prefix}/database'

data_name = 'i_did_it.parquet'
df = pd.read_parquet(f'{data_prefix}/{data_name}')

print(f'src len: {len(df)}')

def merge_dataframe(df):
    ori_length = len(df)
    seg_cnt = 2
    seg_length = ori_length / seg_cnt

    dfs = []

    for i in range(seg_cnt):
        dfs.append(pd.read_parquet(f'{data_prefix}/{i + 1}.parquet'))

    merged_df = dfs[0]
    segments = []
    for i in range(seg_cnt):
        segments.append([int(i * seg_length), int((i + 1) * seg_length)])

    print(segments)

    for seg_id in range(len(segments)):
        l, r = segments[seg_id]

        for i in range(l, r):
            merged_df.loc[i, 'relevant_context'] = dfs[seg_id].loc[i, 'relevant_context']

    merged_df.to_parquet(f'{data_prefix}/i_did_it.parquet')

    return merged_df

merged_df = merge_dataframe(df)
r = verify(merged_df)