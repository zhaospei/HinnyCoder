from pymilvus import MilvusClient, model, db, connections
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
    'metric_type': 'L2',
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

repo_src = open('repos.txt', 'r')

repo_list = [i.strip() for i in repo_src.readlines()]

import hashlib
encoded_repo_list = []
for repo in repo_list:
    encoded_repo_list.append(
        {
            'repo': repo,
            'hashed_repo': f'db_{hashlib.sha256(repo.encode("utf-8")).hexdigest()}',
        }
    )

print(len(encoded_repo_list))

data_type = ['types', 'methods', 'fields']

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

        collections = client.list_collections()
        if (len(collections) == len(data_type)):
            flag = True

            for collection in collections:
                client.load_collection(
                    collection_name = collection,
                )

                res = client.query(
                    collection_name = collection,
                    output_fields = ['count(*)']
                )

                client.release_collection(
                    collection_name = collection,
                )

                rows = res[0]['count(*)']

                f = open(f'{raw_prefix}/{repo["repo"]}_{collection}.json')
                datas = json.load(f)
                f.close()

                if (rows != len(datas)):
                    print(f'invalid db: {repo["repo"]}')
                    flag = False
                    break

                if (rows > max_row):
                    max_row = rows
                    max_db = repo

                print(f'{repo["repo"]}_{collection} row: {rows}')

            if (flag):
                valid.append(repo['repo'])
            else:
                invalid.append(repo['repo'])

        print()

thr = []
for repo in encoded_repo_list:
    q = validate_by_thread(repo, max_row, max_db)
    q.start()

    thr.append(q)

    if ((len(thr) == 10) or (repo == encoded_repo_list[-1])):
        for t in thr:
            t.join()

        thr = []

print(valid)
print(invalid)

print(max_row)
print(max_db)