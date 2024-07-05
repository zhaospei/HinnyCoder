from pymilvus import MilvusClient, model, db, connections, Collection
from threading import Thread

def retrieve(dt, searches, vectors):
    res = client.search(
        collection_name = dt,
        data = vectors,
        limit = 5,
        search_params = search_params,
    )

    # import json
    # res = json.dumps(res, indent = 4)
    # print(res)

    # print(res[0])

    res = client.get(
        collection_name = dt,
        ids = [int(i[0]['id']) for i in res]
    )

    for i in res:
        print(i['name'])

search_params = {
    'metric_type': 'COSINE',
    'params': {
        'nprobe': 1024,
    },
}

uri = 'http://localhost:19530'
raw_prefix = 'data/raw'
db_prefix = 'data/database'

# client = MilvusClient(f'{db_prefix}/{repo}.db')

# searches = [
#     'ping',
#     'testing',
# ]

# embedding_model = init_embedding_model()
# datas = bge_m3_ef.encode_documents(searches)['dense']

# retrieve('types', searches, datas)

import os
import json

valid = []
invalid = []

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

encoded_repo_list, repo_list_map = create_repo_list()
print(f'number of repos: {len(encoded_repo_list)}')

data_type = ['types']

conn = connections.connect(
    host = '127.0.0.1',
    port = '19530',
)

max_row = 0
max_db = 0

class validate_by_thread(Thread):
    def __init__(self, repo, max_row, max_db):
        Thread.__init__(self)

        self.repo = repo
        self.max_row = max_row
        self.max_db = max_db

    def run(self):
        repo = self.repo
        max_row = self.max_row
        max_db = self.max_db

        client = MilvusClient(
            uri = uri,
            db_name = repo['hashed_repo'],
        )

        db.using_database(repo['hashed_repo'])


        collections = client.list_collections()

        # print(f'repo: {repo["hashed_repo"]}, len: {len(collections)}')

        if (len(collections) == len(data_type)):
            flag = True

            for collection_name in collections:
                # connections.connect(repo['hashed_repo'], host = 'localhost', port = '19530')

                # clt = Collection(
                #     name = 'types',
                # )

                # print(f'repo: {repo}, {clt.num_entities}')

                # while (True):
                #     client.load_collection(
                #         collection_name = collection_name,
                #     )

                res = client.query(
                    collection_name = collection_name,
                    output_fields = ['count(*)']
                )

                client.release_collection(
                    collection_name = collection_name,
                )

                rows = res[0]['count(*)']

                print(f'repo: {repo}, {rows}')

                f = open(f'{raw_prefix}/{repo["repo"]}_{collection_name}.json')
                datas = json.load(f)
                f.close()

                if (rows != len(datas)):
                    print(f'invalid db: {repo["repo"]}')
                    flag = False
                    break

                if (rows > max_row):
                    max_row = rows
                    max_db = repo

                print(f'{repo["repo"]}_{collection_name} row: {rows}')

            if (flag):
                valid.append(repo['repo'])
            else:
                invalid.append(repo['repo'])

        print()

def validate(repo, max_row, max_db):
    client = MilvusClient(
        uri = uri,
        db_name = repo['hashed_repo'],
    )

    db.using_database(repo['hashed_repo'])


    collections = client.list_collections()

    # print(f'repo: {repo["hashed_repo"]}, len: {len(collections)}')

    if (len(collections) == len(data_type)):
        flag = True

        for collection_name in collections:
            # connections.connect(repo['hashed_repo'], host = 'localhost', port = '19530')

            # clt = Collection(
            #     name = 'types',
            # )

            # print(f'repo: {repo}, {clt.num_entities}')

            while (True):
                try:
                    client.load_collection(
                        collection_name = collection_name,
                    )

                    break
                except Exception as e:
                    pass

            res = client.query(
                collection_name = collection_name,
                output_fields = ['count(*)']
            )

            client.release_collection(
                collection_name = collection_name,
            )

            rows = res[0]['count(*)']

            # print(f'repo: {repo["repo"]}, row: {rows}')

            f = open(f'{raw_prefix}/{repo["repo"]}_{collection_name}.json')
            datas = json.load(f)
            f.close()

            if (rows != len(datas)):
                print(f'invalid db: {repo["repo"]}')
                flag = False
                break

            if (rows > max_row):
                max_row = rows
                max_db = repo

            print(f'{repo["repo"]}_{collection_name} row: {rows}')

        if (flag):
            valid.append(repo['repo'])
        else:
            invalid.append(repo['repo'])

    print()

# thr = []
# for repo in encoded_repo_list:
#     q = validate_by_thread(repo, max_row, max_db)
#     q.start()

#     thr.append(q)

#     if ((len(thr) == 10) or (repo == encoded_repo_list[-1])):
#         for t in thr:
#             t.join()

#         thr = []

cnt = 0
for repo in encoded_repo_list:
    validate(repo, max_row, max_db)

    cnt += 1

    if (cnt == 1):
        break

print(valid)
print(invalid)

print(max_row)
print(max_db)