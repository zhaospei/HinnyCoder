from pymilvus import MilvusClient, model
from threading import Thread
from tqdm import tqdm
import pandas as pd
import argparse
import json
import time


def scan_repo_list():
    import os

    # List to store the modified filenames
    modified_filenames = set()

    # Directory containing the files
    directory = 'data/raw'

    # Loop through each file in the specified directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            # Remove the specified substrings from the filename
            new_filename = filename.replace('_methods', '').replace('_fields', '').replace('_types', '').replace('_method', '').replace('_field', '').replace('_type', '')
            # Remove the '.json' extension
            new_filename = new_filename[:-5]
            # Add the modified filename to the list
            modified_filenames.add(new_filename)

    # Display the modified filenames

    modified_filenames = list(modified_filenames)

    f = open('repos.txt', 'w')

    for i in modified_filenames:
        f.write(i + '\n')

    f.close()

def create_repo_list(scan_db = False):
    if (scan_db):
        scan_repo_list()

    repo_src = open('repos.txt', 'r')
    repo_list = [i.strip() for i in repo_src.readlines()]
    repo_src.close()

    # clean_databases()
    import hashlib
    encoded_repo_list = []
    for repo in repo_list:
        encoded_repo_list.append(
            {
                'repo': repo,
                'hashed_repo': f'db_{hashlib.sha256(repo.encode("utf-8")).hexdigest()}',
            }
        )

    repo_list_map = {}
    for repo in encoded_repo_list:
        repo_list_map[repo['repo']] = repo['hashed_repo']

    return encoded_repo_list, repo_list_map

uri = 'http://localhost:19530'
data_prefix = 'data'
raw_prefix = f'{data_prefix}/raw'
db_prefix = f'{data_prefix}/database'

data_type = ['types']
search_params = {
    'metric_type': 'L2',
    'params': {
        'nprobe': 1024,
    },
}

embedding_model = model.hybrid.BGEM3EmbeddingFunction(
    model_name = 'BAAI/bge-m3',
    device = 'cuda:0',
    use_fp16 = False,
)

def retrieve(client, db_name, embedded_retrieval_elements):
        client = MilvusClient(
            uri = uri,
            db_name = db_name,
        )

        MAX_TOKEN = 3000
        current_tokens = 0

        relevant_context = ''
        for dt in data_type:
            while (True):
                try:
                    client.load_collection(
                        collection_name = dt,
                    )

                    break
                except Exception as e:
                    pass

            if (dt not in embedded_retrieval_elements):
                continue

            all_res = []
            things_we_need_to_find = embedded_retrieval_elements[dt]
            # optimize here!!!

            retrieved_candidates = client.search(
                collection_name = dt,
                data = things_we_need_to_find,
                limit = 3,
                search_params = search_params,
            )

            for candidate in retrieved_candidates:
                ids = [int(candidate[0]['id'])]

                res = client.get(
                    collection_name = dt,
                    ids = ids,
                )

                all_res.append(res[0])

            client.release_collection(
                collection_name = dt,
            )

            f = open(all_res[0]['data_path'], 'r')
            datas = json.load(f)
            f.close()

            for i in all_res:
                tokens = None
                if (dt == 'types'):
                    tokens = datas[i['id']]['abstract'].split()
                else:
                    tokens = datas[i['id']]['raw'].split()

                if (current_tokens + len(tokens) > MAX_TOKEN):
                    continue

                current_tokens += len(tokens)

                if (dt == 'types'):
                    relevant_context += datas[i['id']]['abstract']
                else:
                    relevant_context += datas[i['id']]['raw']

        client.close()

        return relevant_context

class query_by_thread(Thread):
    def __init__(self, client, db_name, embedded_retrieval_elements, testcase, df):
        Thread.__init__(self)
        self.client = client
        self.db_name = db_name
        self.embedded_retrieval_elements = embedded_retrieval_elements
        self.testcase = testcase
        self.df = df

    def run(self):
        res = retrieve(self.client, self.db_name, self.embedded_retrieval_elements)

        self.df.loc[self.testcase, 'relevant_context'] = res

class create_work_queue_by_thread(Thread):
    def __init__(self, id, row, work_queue, repo_list_map):
        Thread.__init__(self)
        self.id = id
        self.row = row
        self.work_queue = work_queue
        self.repo_list_map = repo_list_map

    def run(self):
        row = self.row
        work_queue = self.work_queue
        repo_list_map = self.repo_list_map
        id = self.id

        db_name = repo_list_map[row['proj_name']]
        retrieval_elements = row['retrieval_element']
        embedded_retrieval_elements = {}

        for element in retrieval_elements:
            if (len(retrieval_elements[element]) == 0):
                continue

            c = []
            for i in retrieval_elements[element]:
                if (len(i) == 0):
                    continue

                c.append(i)

            if (len(c) == 0):
                continue

            embedded_retrieval_elements[element] = embedding_model.encode_documents(list(retrieval_elements[element]))['dense']

        work_queue[db_name].append(
            {
                'id': id,
                'db_name': db_name,
                'embedded_retrieval_elements': embedded_retrieval_elements,
            }
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--scan_databases',
        action = 'store_true',
        help = 'scan for new databases'
    )

    parser.add_argument(
        '--l',
        type = int,
        help = 'lower bound of the dataset (inclusive) ( [l, r) )',
        default = 0,
    )

    parser.add_argument(
        '--r',
        type = int,
        help = 'upper bound of the dataset (exclusive) ( [l, r) )',
        default = 10000000000000000,
    )

    parser.add_argument(
        '--src_name',
        type = str,
        help = 'data source file name',
        default = 'source.parquet',
    )

    parser.add_argument(
        '--name',
        type = str,
        help = 'saved file name',
        default = 'i_did_it.parquet',
    )

    args = parser.parse_args()

    scan_db = False
    if (args.scan_databases):
        scan_db = True

    encoded_repo_list, repo_list_map = create_repo_list(scan_db)
    print(len(encoded_repo_list))

    data_name = args.src_name
    df = pd.read_parquet(f'{data_prefix}/{data_name}')
    res_name = args.name

    thread_cnt = len(encoded_repo_list)
    clients = []
    for i in range(thread_cnt):
        clients.append(
            MilvusClient(
                uri = uri,
            )
        )

    work_queue = {}
    for (key, value) in repo_list_map.items():
        work_queue[value] = []

    l = args.l
    l = max(0, l)
    l = min(l, len(df) - 1)
    r = args.r
    r = max(0, r)
    r = min(r, len(df))

    threads = []
    ids = [i for i in range(l, r)]
    # ids = [1, 27, 37, 51, 67, 74, 104, 115, 120, 122, 129, 139, 152, 159, 162, 186, 189, 190, 192, 194, 208, 209, 210, 211, 215, 217, 224, 230, 235, 236, 237, 239, 240, 241, 246, 251, 256, 268, 296, 331, 337, 342, 364, 365, 369, 377, 382, 386, 405, 416, 424, 432, 433, 438, 447, 448, 451, 453, 454, 457, 460, 464, 465, 466, 467, 468, 471, 479, 483, 486, 487, 488, 491, 494, 495, 496, 497]
    print(l, r)
    for i in tqdm(ids, 'build work queue'):
        row = df.iloc[i]

        b = create_work_queue_by_thread(
            id = i,
            row = row,
            work_queue = work_queue,
            repo_list_map = repo_list_map,
        )
        b.start()
        threads.append(b)

        if ((len(threads) == thread_cnt) or (i == ids[-1])):
            for thread in threads:
                thread.join()

            threads = []

    rows = 0
    for (key, value) in work_queue.items():
        rows += len(value)

    print(f'number of rows: {rows}')

    end_flag = True
    while(end_flag):
        thread_i = 0
        threads = []

        working_on = []
        for key in work_queue:
            if (len(work_queue[key]) > 0):
                q = query_by_thread(
                    client = clients[thread_i % thread_cnt],
                    db_name = work_queue[key][-1]['db_name'],
                    embedded_retrieval_elements = work_queue[key][-1]['embedded_retrieval_elements'],
                    testcase = work_queue[key][-1]['id'],
                    df = df,
                )

                thread_i += 1

                threads.append(q)

                working_on.append(work_queue[key][-1]['id'])

                work_queue[key].pop()

        rows -= len(working_on)
        print(f'working on: {working_on}')
        print(f'remaining: {rows}')
        print()

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        df.to_parquet(f'{data_prefix}/{res_name}')

        end_flag = False
        for key in work_queue:
            end_flag = end_flag or (len(work_queue[key]) > 0)

    # for key in work_queue:
    #     queue = work_queue[key]

    #     working_on = []

    #     dt_work_queue = {
    #         'types': [],
    #         'methods': [],
    #         'fields': [],
    #     }
    #     for testcase in queue:
    #         dt_work_queue[testcase['']]

    #     rows -= len(working_on)
    #     print(f'working on: {working_on}')
    #     print(f'remaining: {rows}')
    #     print()

    #     for thread in threads:
    #         thread.start()

    #     for thread in threads:
    #         thread.join()

    #     df.to_parquet(f'{data_prefix}/{res_name}')

    #     end_flag = False
    #     for key in work_queue:
    #         end_flag = end_flag or (len(work_queue[key]) > 0)

if (__name__ == '__main__'):
    main()