from pymilvus import MilvusClient, DataType, model

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

search_params = {
    'metric_type': 'L2',
    'params': {
        'nprobe': 1024,
    },
}

uri = 'http://localhost:19530'
raw_prefix = 'data/raw'
db_prefix = 'data/database'

def retrieve(client, dt, vectors):
    client.load_collection(
        collection_name = dt,
    )

    all_res = []
    for vector in vectors:
        res = client.search(
            collection_name = dt,
            data = [vector],
            limit = 5,
            search_params = search_params,
        )

        ids = [int(i[0]['id']) for i in res]

        res = client.get(
            collection_name = dt,
            ids = ids,
        )

        all_res.append(res[0])

    client.release_collection(
        collection_name = dt,
    )

    import json
    f = open(all_res[0]['data_path'], 'r')
    datas = json.load(f)
    f.close()

    ret = []
    for i in all_res:
        ret.append(datas[i['id']])

    return ret

data_type = ['types', 'methods', 'fields']

searches = {
    'types': [
        'HashMap<String,Object>', 'ApplicationContext', 'FrontendAuthService', 'User', 'String',
    ],

    'methods': [
        'loginUsingId', 'getId', 'url', 'put', 'publishEvent', 'getEmail', 'getIpAddress', 'ua',
    ],

    'fields': [
        'data', 'ctx', 'authService', 'user', 'token',
    ],
}

repo = encoded_repo_list[14]

bge_m3_ef = model.hybrid.BGEM3EmbeddingFunction(
    model_name = 'BAAI/bge-m3',
    device = 'cuda:0',
    use_fp16 = False,
)

client = MilvusClient(
    uri = uri,
    db_name = repo['hashed_repo'],
)

f = open('res.json', 'w')

import json
writer = {}

for (dt, value) in searches.items():
    embedded_searches = bge_m3_ef.encode_documents(value)['dense']

    writer[dt] = []

    res = retrieve(client, dt, embedded_searches)

    print(repo['repo'] + f'_{dt}')
    for i in range(len(value)):
        writer[dt].append(
            {
                value[i]: res[i],
            },
        )

    print()

json.dump(writer, f, indent = 4)

f.close()