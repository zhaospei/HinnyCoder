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

from pymilvus import MilvusClient, DataType, model

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

def init_embedding_model():
    embedding_model = model.hybrid.BGEM3EmbeddingFunction(
        model_name = 'BAAI/bge-m3',
        device = 'cuda:0',
        use_fp16 = False,
    )

    return embedding_model

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
        # 'nprobe': 10,
    },
}

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

raw_prefix = 'data/raw'
db_prefix = 'data/database'
data_type = ['types', 'methods', 'fields']

min_length = 70000000000000000000000
max_length = 0
mean_length = 0
cnt = 0

for repo in repo_list:
    data_dir = f'{raw_prefix}/{repo}_{data_type[0]}.json'

    f = open(data_dir)
    datas = json.load(f)
    f.close()

    for i in datas:
        min_length = min(min_length, len(i['abstract']))
        max_length = max(max_length, len(i['abstract']))
        mean_length += len(i['abstract'])
        cnt += 1

    break

print(f'min: {min_length}')
print(f'max: {max_length}')
print(f'mean: {mean_length}')
print(f'cnt: {cnt}')