from pymilvus import MilvusClient, model
from threading import Thread
from tqdm import tqdm
import pandas as pd
import argparse
import json
import os

uri = 'http://localhost:19530'
data_prefix = 'data'
raw_prefix = f'{data_prefix}/raw'
db_prefix = f'{data_prefix}/database'

data_type = ['types', 'methods', 'similar_methods',]
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

def scan_repo_list():
    import os

    # List to store the modified filenames
    modified_filenames = set()

    # Directory containing the files
    directory = raw_prefix

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

def retrieve(client, db_name, proj_name, relative_path, embedded_retrieval_elements):
    client = MilvusClient(
        uri = uri,
        db_name = db_name,
    )

    relevant_context = ''
    relevant_context_no_cmt = ''
    current_relative_path = os.path.join(proj_name, relative_path)
    retrieved_names = {}
    retrieved_types = []
    retrieved_methods = []
    similar_methods = []
    retrieved_name_set = set()
    for dt in data_type:
        if (dt not in embedded_retrieval_elements):
            continue

        retrieved_names[dt] = []

        collection_name = dt
        if (dt == 'similar_methods'):
            collection_name = 'methods'

        while(True):
            try:
                client.load_collection(
                    collection_name = collection_name,
                )

                break
            except Exception as e:
                pass

        all_res = []
        names = list(embedded_retrieval_elements[dt].keys())
        things_we_need_to_find = [embedded_retrieval_elements[dt][key] for key in names]
        # optimize here!!!

        retrieved_candidates = client.search(
            collection_name = collection_name,
            data = things_we_need_to_find,
            limit = 3,
            search_params = search_params,
        )

        if (len(retrieved_candidates) != len(things_we_need_to_find)):
            print('t lay. m? sao loi~ dc hay v')
            print('-' * 100)

            return

        for i in range(len(retrieved_candidates)):
            candidates = retrieved_candidates[i]
            ids = [int(candidates[j]['id']) for j in range(len(candidates))]

            wres = []
            for ai_di in ids:
                res = client.get(
                    collection_name = collection_name,
                    ids = [ai_di],
                )

                wres.append(res[0])

            all_res.append(
                {
                    names[i]: wres,
                }
            )

        client.release_collection(
            collection_name = collection_name,
        )

        f = open(all_res[0][names[0]][0]['data_path'], 'r')
        datas = json.load(f)
        f.close()

        for i in range(len(all_res)):
            name = names[i]
            bundled_data = all_res[i][name]
            data = None

            retrieved_name = ''
            for r in bundled_data:
                r_relative_path = datas[r['id']]['relative_path']

                if (r_relative_path == current_relative_path):
                    continue
                else:
                    data = r
                    retrieved_name = datas[data['id']]['name']

                    break

            retrieved_names[dt].append(
                {
                    name: retrieved_name,
                }
            )

            if (data is None):
                continue

            if (dt == 'types'):
                if (retrieved_name in retrieved_name_set):
                    continue
                else:
                    retrieved_name_set.add(retrieved_name)

                # print(proj_name, datas[data['id']].keys())

                raw_body = datas[data['id']]['abstract']
                raw_body_no_cmt = ''

                relevant_context += raw_body
                if ('abstract_compact' in datas[data['id']].keys()):
                    raw_body_no_cmt = datas[data['id']]['abstract_compact']
                    relevant_context_no_cmt += raw_body_no_cmt

                retrieved_types.append(
                    {
                        name: {
                            'retrieved_name': retrieved_name,
                            'raw_body': raw_body,
                            'raw_body_no_cmt': raw_body_no_cmt,
                        },
                    },
                )
            else:
                raw_body = datas[data['id']]['raw']

                relevant_context += raw_body
                # no data for no cmt
                relevant_context_no_cmt += raw_body

                if (dt == 'methods'):
                    retrieved_methods.append(
                        {
                            name: {
                                'retrieved_name': retrieved_name,
                                'raw_body': raw_body,
                            },
                        },
                    )
                elif (dt == 'similar_methods'):
                    similar_methods.append(
                        {
                            name: {
                                'retrieved_name': retrieved_name,
                                'raw_body': raw_body,
                            },
                        },
                    )

    return relevant_context, relevant_context_no_cmt, retrieved_names, retrieved_types, retrieved_methods, similar_methods

class query_by_thread(Thread):
    def __init__(self, client, db_name, embedded_retrieval_elements, testcase, df):
        Thread.__init__(self)
        self.client = client
        self.db_name = db_name
        self.embedded_retrieval_elements = embedded_retrieval_elements
        self.testcase = testcase
        self.df = df

    def run(self):
        proj_name = self.df.iloc[self.testcase]['proj_name']
        relative_path = self.df.iloc[self.testcase]['relative_path']
        res, res_no_cmt, retrieved_names, retrieved_types, retrieved_methods, similar_methods = retrieve(
            self.client, self.db_name, proj_name, relative_path, self.embedded_retrieval_elements
        )

        self.df.at[self.testcase, 'relevant_context'] = res
        self.df.at[self.testcase, 'relevant_context_no_cmt'] = res_no_cmt
        self.df.at[self.testcase, 'retrieved_names'] = json.dumps(retrieved_names)
        self.df.at[self.testcase, 'retrieved_types'] = json.dumps(retrieved_types)
        self.df.at[self.testcase, 'retrieved_methods'] = json.dumps(retrieved_methods)
        self.df.at[self.testcase, 'similar_methods'] = json.dumps(similar_methods)

class create_work_queue_by_thread(Thread):
    def __init__(self, id, row, work_queue, repo_list_map, retrieval_column):
        Thread.__init__(self)
        self.id = id
        self.row = row
        self.work_queue = work_queue
        self.repo_list_map = repo_list_map
        self.retrieval_column = retrieval_column

    def run(self):
        row = self.row
        work_queue = self.work_queue
        repo_list_map = self.repo_list_map
        id = self.id
        retrieval_column = self.retrieval_column

        db_name = repo_list_map[row['proj_name']]
        retrieval_elements = row[retrieval_column]
        embedded_retrieval_elements = {}

        for element in data_type:
            if (element not in retrieval_elements.keys()):
                continue

            if (len(retrieval_elements[element]) == 0):
                continue

            c = []
            for i in retrieval_elements[element]:
                if (len(i) == 0):
                    continue

                c.append(i)

            if (len(c) == 0):
                continue

            embedded_retrieval_elements[element] = {}
            embedded_retrieval_element = embedding_model.encode_queries(list(retrieval_elements[element]))['dense']

            # embedded_retrieval_element = []
            # for i_name in list(retrieval_elements[element]):
            #     embedded_retrieval_element.append(embedding_model.encode_queries([i_name])['dense'][0])

            for i in range(len(retrieval_elements[element])):
                raw_data_name = retrieval_elements[element][i]
                embedded_retrieval_elements[element][raw_data_name] = embedded_retrieval_element[i]

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
        '--reset',
        action = 'store_true',
        help = 'reset all the output columns'
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

    parser.add_argument(
        '--retrieval_column',
        type = str,
        help = 'column contains the retrieval elements',
        default = 'retrieval_element',
    )

    args = parser.parse_args()

    scan_db = False
    if (args.scan_databases):
        scan_db = True

    encoded_repo_list, repo_list_map = create_repo_list(scan_db)
    print(len(encoded_repo_list))

    data_name = args.src_name
    df = pd.read_parquet(f'{data_prefix}/{data_name}')

    output_columns = [
        'relevant_context', 'relevant_context_no_cmt', 'retrieved_names', 'retrieved_types', 'retrieved_methods', 'similar_methods',
    ]
    for col in output_columns:
        if (col not in df.columns):
            df[col] = None
    if (args.reset):
        for col in output_columns:
            df[col] = None

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
    print(l, r)
    for i in tqdm(ids, 'build work queue'):
        row = df.iloc[i]

        b = create_work_queue_by_thread(
            id = i,
            row = row,
            work_queue = work_queue,
            repo_list_map = repo_list_map,
            retrieval_column = args.retrieval_column
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

    print(f'number of rows: {rows}\n')

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