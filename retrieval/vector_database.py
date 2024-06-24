import os

# List to store the modified filenames
modified_filenames = set()

# Directory containing the files
directory = 'data/raw'

# Loop through each file in the specified directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        # Remove the specified substrings from the filename
        new_filename = filename.replace('_methods', '').replace('_fields', '').replace('_types', '')
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

repo_src = open('repos.txt', 'r')

repo_list = [i.strip() for i in repo_src.readlines()]

print(len(repo_list))

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

    schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
    schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'implements', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'extend', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'abstract', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

def create_methods_schema():
    schema = MilvusClient.create_schema (
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)

    schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
    schema.add_field(field_name = 'class', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'return_type', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'parameters', datatype = DataType.JSON)
    schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

def create_fields_schema():
    schema = MilvusClient.create_schema (
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)

    schema.add_field(field_name = 'relative_path', datatype = DataType.VARCHAR, max_length = 5000)
    schema.add_field(field_name = 'class', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'type', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'modifiers', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 200)
    schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

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

bge_m3_ef = model.hybrid.BGEM3EmbeddingFunction(
    model_name = 'BAAI/bge-m3',
    device = 'cuda:0',
    use_fp16 = False,
)

from tqdm import tqdm

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
        vector_embeddings = bge_m3_ef.encode_documents(names)
        dense_vectors = vector_embeddings['dense']

        for i in tqdm(range(len(datas)), desc = f'{self.repo}_{self.dt}'):
            raw_data = datas[i]

            lacking = valid_keys[self.dt] - set(raw_data.keys())

            for lack in lacking:
                raw_data[lack] = dummy_vals[lack]

            raw_data['id'] = i
            raw_data['vector'] = dense_vectors[i]

            self.client.insert(
                collection_name = self.dt,
                data = raw_data,
            )

from tqdm import tqdm

def insert_data(repo, dt, client):
    data_dir = f'{raw_prefix}/{repo}_{dt}.json'

    f = open(data_dir)
    datas = json.load(f)
    f.close()

    names = [data['name'] for data in datas]
    vector_embeddings = bge_m3_ef.encode_documents(names)
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

for repo in repo_list:
    print(repo)

    client = MilvusClient(f'{db_prefix}/{repo}.db')

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name = 'vector',
        metric_type = 'L2',
        index_type = 'FLAT',
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

    for dt in data_type:
        inserter = insert_data_by_thread(repo, dt, client)
        inserter.start()