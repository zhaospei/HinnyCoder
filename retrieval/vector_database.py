repo_src = open('repos.txt', 'r')
repo_list = [i.strip() for i in repo_src.readlines()]

# excluded_repos = ['Kong_unirest-java', 'subhra74_snowflake', 'elunez_eladmin', 'mapstruct_mapstruct', 'eirslett_frontend-maven-plugin', 'ainilili_ratel', 'obsidiandynamics_kafdrop', 'DerekYRC_mini-spring', 'graphhopper_graphhopper', 'javamelody_javamelody', 'jeecgboot_jeecg-boot', 'YunaiV_ruoyi-vue-pro', 'PlayEdu_PlayEdu', 'docker-java_docker-java', 'google_truth', 'qiujiayu_AutoLoadCache', 'Pay-Group_best-pay-sdk', 'zhkl0228_unidbg']
# repo_list = list(set(repo_list) - set(excluded_repos))

print(len(repo_list))
# print(repo_list)

from pymilvus import MilvusClient, DataType, model
from threading import Thread
import json

def create_types_schema():
    schema = MilvusClient.create_schema (
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
    # schema.add_field(field_name = 'abstract', datatype = DataType.VARCHAR, max_length = 65535)
    # schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    schema.add_field(field_name = 'data', datatype = DataType.JSON)

    return schema

def create_methods_schema():
    schema = MilvusClient.create_schema (
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

    schema.add_field(field_name = 'data', datatype = DataType.JSON)

    return schema

def create_fields_schema():
    schema = MilvusClient.create_schema (
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

    schema.add_field(field_name = 'data', datatype = DataType.JSON)

    return schema

schemas = {
    'types': create_types_schema(),
    'methods': create_methods_schema(),
    'fields': create_fields_schema(),
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

from tqdm import tqdm

def init_embedding_model():
    embedding_model = model.hybrid.BGEM3EmbeddingFunction(
        model_name = 'BAAI/bge-m3',
        device = 'cuda:0',
        use_fp16 = False,
    )

embedding_model = model.hybrid.BGEM3EmbeddingFunction(
    model_name = 'BAAI/bge-m3',
    device = 'cuda:0',
    use_fp16 = False,
)

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
            raw_data = datas[i]
            inserted_data = {}

            lacking = valid_keys[self.dt] - set(raw_data.keys())

            for lack in lacking:
                raw_data[lack] = dummy_vals[lack]

            inserted_data['id'] = i
            inserted_data['vector'] = dense_vectors[i]
            inserted_data['data'] = raw_data

            self.client.insert(
                collection_name = self.dt,
                data = inserted_data,
            )

def insert_data(repo, dt, client):
    data_dir = f'{raw_prefix}/{repo}_{dt}.json'

    f = open(data_dir)
    datas = json.load(f)
    f.close()

    names = [data['name'] for data in datas]
    vector_embeddings = embedding_model.encode_documents(names)
    dense_vectors = vector_embeddings['dense']

    for i in tqdm(range(len(datas)), desc = dt):
        raw_data = datas[i]

        lacking = valid_keys[dt] - set(raw_data.keys())

        for lack in lacking:
            raw_data[lack] = dummy_vals[lack]

        raw_data['id'] = i
        raw_data['vector'] = dense_vectors[i]

        client.insert(
            collection_name = dt,
            data = raw_data,
        )

raw_prefix = 'data/raw'
db_prefix = 'data/database'

def create_database(repo):
    print(repo)

    client = MilvusClient(f'{db_prefix}/{repo}.db')

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name = 'vector',
        metric_type = 'L2',
        index_type = 'HNSW',
        params = {},
    )

    data_type = ['types', 'methods', 'fields']

    for dt in data_type:
        if client.has_collection(collection_name = dt):
            client.drop_collection(collection_name = dt)

        client.create_collection(
            collection_name = dt,
            schema = schemas[dt],
            index_params = index_params,
        )

    pool = []
    for dt in data_type:
        inserter = insert_data_by_thread(repo, dt, client)
        pool.append(inserter)

    for inserter in pool:
        inserter.start()

    for inserter in pool:
        inserter.join()

for repo in repo_list:
    create_database(repo)

    break
