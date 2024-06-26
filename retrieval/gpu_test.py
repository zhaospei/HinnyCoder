from pymilvus import MilvusClient, DataType, model, connections, db, Collection, FieldSchema, CollectionSchema
from threading import Thread
from tqdm import tqdm
import json

conn = connections.connect(host = '127.0.0.1', port = 19530)

uri = 'http://localhost:19530'
raw_prefix = 'data/raw'
db_prefix = 'data/database'

repo_src = open('repos.txt', 'r')
repo_list = [i.strip() for i in repo_src.readlines()]

def create_databases(repo_list):
    repo_list = [i.strip().replace('-', '_') for i in repo_list]

    db_list = db.list_database()

    for repo in repo_list:
        if (repo in db_list):
            continue

            client = MilvusClient(
                uri = uri,
                db_name = repo,
            )

            collections = client.list_collections()

            for collection in collections:
                client.drop_collection(collection_name = collection)

            db.drop_database(repo)

        db.create_database(repo)

def create_blank_databases(repo_list):
    db_list = db.list_database()

    for repo in repo_list:
        if (repo in db_list):
            client = MilvusClient(
                uri = uri,
                db_name = repo,
            )

            collections = client.list_collections()

            for collection in collections:
                client.drop_collection(collection_name = collection)

            db.drop_database(repo)

        db.create_database(repo)

def clean_databases():
    db_list = db.list_database()

    for db_name in db_list:
        if (db_name == 'default'):
            continue

        client = MilvusClient(
            uri = uri,
            db_name = db_name,
        )

        collections = client.list_collections()

        for collection in collections:
            client.drop_collection(collection_name = collection)

        db.drop_database(db_name)

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
print(len(encoded_repo_list))
create_blank_databases([i['hashed_repo'] for i in encoded_repo_list])

def create_types_schema():
    schema = MilvusClient.create_schema(
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)

    # schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
    # schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'implements', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'extend', datatype = DataType.VARCHAR, max_length = 200)
    # # schema.add_field(field_name = 'abstract', datatype = DataType.VARCHAR, max_length = 65535)
    # schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    # schema.add_field(field_name = 'data', datatype = DataType.JSON)

    schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

def create_methods_schema():
    schema = MilvusClient.create_schema(
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)

    # schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
    # schema.add_field(field_name = 'class', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'return_type', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'parameters', datatype = DataType.JSON)
    # schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    # schema.add_field(field_name = 'data', datatype = DataType.JSON)

    schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

def create_fields_schema():
    schema = MilvusClient.create_schema(
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)

    # schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
    # schema.add_field(field_name = 'class', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'type', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
    # schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    # schema.add_field(field_name = 'data', datatype = DataType.JSON)

    schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

schema = MilvusClient.create_schema(
    auto_id = False,
    enable_dynamic_fields = True,
)

schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)

# schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
# schema.add_field(field_name = 'class', datatype = DataType.VARCHAR, max_length = 200)
# schema.add_field(field_name = 'type', datatype = DataType.VARCHAR, max_length = 200)
# schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
# schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
# schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

# schema.add_field(field_name = 'data', datatype = DataType.JSON)

schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

schemas = {
    # 'types': create_types_schema(),
    # 'methods': create_methods_schema(),
    # 'fields': create_fields_schema(),
    'types': schema,
    'methods': schema,
    'fields': schema,
}

valid_keys = {
    'types': {'relative_path', 'name', 'modifiers', 'extend', 'implements', 'raw', 'abstract'},
    'methods': {'relative_path', 'class', 'name', 'return_type', 'modifiers', 'parameters', 'raw'},
    'fields': {'relative_path', 'class', 'type', 'modifiers', 'name', 'raw'},
}

dummy_vals = {
    'name': '',
    'abstract': '',
    'parameters': [],
    'relative_path': '',
    'modifiers': '',
    'extend': '',
    'type': '',
    'raw': '',
    'implements': '',
    'class': '',
    'return_type': '',
}

class insert_data_by_thread(Thread):
    def __init__(self, repo, dt, client):
        Thread.__init__(self)
        self.client = client
        self.repo = repo
        self.dt = dt
        self.data_dir = f'{raw_prefix}/{repo}_{dt}.json'

    def run(self):
        data_dir = self.data_dir

        f = open(data_dir)
        datas = json.load(f)
        f.close()

        names = [data['name'] for data in datas]
        vector_embeddings = embedding_model.encode_documents(names)
        dense_vectors = vector_embeddings['dense']

        for i in tqdm(range(len(datas)), desc = f'{self.repo}_{self.dt}'):
            # raw_data = datas[i]

            # lacking = valid_keys[self.dt] - set(raw_data.keys())

            # for lack in lacking:
            #     raw_data[lack] = dummy_vals[lack]

            inserted_data = {}
            inserted_data['id'] = i
            inserted_data['vector'] = dense_vectors[i]
            inserted_data['data_path'] = data_dir

            self.client.insert(
                collection_name = self.dt,
                data = inserted_data,
            )

def create_database(encoded_repo):
    print(encoded_repo['repo'])

    client = MilvusClient(
        uri = uri,
        db_name = encoded_repo['hashed_repo'],
    )

    # index_params = {
    #     # 'field_name': 'vector',
    #     'metric_type': 'L2',
    #     'index_type': 'GPU_IVF_FLAT',
    #     'params': {
    #         'nlist': 1024,
    #     },
    # }

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name = 'vector',
        metric_type = 'L2',
        index_type = 'GPU_IVF_FLAT',
        params = {
            'nlist': 1024,
        },
    )

    data_type = ['types', 'methods', 'fields']

    for dt in data_type:
        if client.has_collection(collection_name = dt):
            client.drop_collection(collection_name = dt)

        client.create_collection(
            collection_name = dt,
            schema = schemas[dt],
        )

        client.create_index(
            collection_name = dt,
            # field_name = 'vector',
            index_params = index_params,
        )

    pool = []
    for dt in data_type:
        inserter = insert_data_by_thread(encoded_repo['repo'], dt, client)
        pool.append(inserter)

    for inserter in pool:
        inserter.start()

    for inserter in pool:
        inserter.join()

embedding_model = model.hybrid.BGEM3EmbeddingFunction(model_name = 'BAAI/bge-m3', device = 'cuda:0', use_fp16 = False,)

for encoded_repo in encoded_repo_list:
    create_database(encoded_repo)