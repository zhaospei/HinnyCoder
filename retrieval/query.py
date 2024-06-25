from pymilvus import MilvusClient, DataType, model

repo_src = open('repos.txt', 'r')

repo_list = [i.strip() for i in repo_src.readlines()]

print(len(repo_list))

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

search_params = {
    'metric_type': 'L2',
    'params': {
        'nprobe': 10,
    },
}

raw_prefix = 'data/raw'
db_prefix = 'data/database'

repo = 'docker-java_docker-java'

client = MilvusClient(f'{db_prefix}/{repo}.db')

searches = [
    'ping',
]

datas = bge_m3_ef.encode_documents(searches)['dense']

res = client.search(
    collection_name = 'types',
    data = datas,
    limit = 5,
    search_params = search_params,
)

import json

res = json.dumps(res, indent = 4)

print(res)

queries = client.query(
    collection_name = 'types',
    # filter = '1 <= id <= 100',
    filter = 'id == 619',
)

for i in queries:
    print(i['name'])