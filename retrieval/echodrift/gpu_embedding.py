from pymilvus import MilvusClient, DataType, model, connections, db, list_collections
from tqdm import tqdm
import argparse
import json

uri = 'http://localhost:19530'
data_raw = "/home/phatnt/code/github/HinnyCoder/retrieval/data/raw"
database = "/home/phatnt/code/github/HinnyCoder/retrieval/data/database"
connections.connect(alias="default", host = '127.0.0.1', port = 19530)


# create a repo_list and hash it for database name
def create_repo_list(repos_storage: str):
    with open(repos_storage, 'r') as f:
        repo_list = list(map(lambda line: line.strip(), f.readlines()))
    import hashlib
    encoded_repo_list = [
        {
            'repo': repo,
            'hashed_repo': f'db_{hashlib.sha256(repo.encode("utf-8")).hexdigest()}',
        }
        for repo in repo_list
    ]
    repo_list_map = {}
    for repo in encoded_repo_list:
        repo_list_map[repo['hashed_repo']] = repo['repo']
    return encoded_repo_list, repo_list_map


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
        client.close()

# create database, skip existing databases
def create_databases(repo_list):
    db_list = db.list_database()

    for repo in repo_list:
        if (repo in db_list):
            continue

        db.create_database(repo)

# create database, remove existing databases
def create_blank_databases(repo_list):
    clean_databases()
    for repo in repo_list:
        db.create_database(repo)


# create a generic schema
def create_generic_schema():
    schema = MilvusClient.create_schema(
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)
    schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 256)
    schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 1024)

    return schema

def create_framework():
    default_schema = create_generic_schema()
    schemas = {
        'types': default_schema,
    }
    return schemas


def create_database(encoded_repo: dict, schemas, embedding_model):
    # Didn't close connect may be result in multiple connection to database
    
    # try:
    hashed_repo = encoded_repo["hashed_repo"]
    repo = encoded_repo["repo"]
    print("Processing:", repo)
    client = MilvusClient(
        uri = uri,
        db_name = hashed_repo,
    )

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name = 'vector',
        metric_type = 'L2',
        index_type = 'GPU_IVF_FLAT',
        params = {
            'nlist': 1024,
        },
    )
    
    if client.has_collection(collection_name = "types"):
        client.drop_collection(collection_name = "types")

    client.create_collection(
        collection_name = "types",
        schema = schemas["types"],
    )

    client.create_index(
        collection_name = "types",
        index_params = index_params,
    )
    repo_info_url = f"{data_raw}/{repo}_types.json" 
    with open(repo_info_url, 'r') as f: 
        datas = json.load(f)

    names = [data['name'] for data in datas]
    vector_embeddings = embedding_model.encode_documents(names)
    dense_vectors = vector_embeddings['dense']

    for i in tqdm(range(len(datas)), desc = f'{repo}'):
        inserted_data = {
            'id': i,
            'name': names[i],
            'vector': dense_vectors[i],
            'data_path': repo_info_url
        }
        client.insert(
            collection_name = "types",
            data = inserted_data,
        )
    # client.close()
    collections = list_collections()
    print("Collections:", collections)
    # except Exception as e:
    #     pass

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--create_blank_databases',
        action = 'store_true',
        help = 'create blank databases'
    )

    args = parser.parse_args()

    encoded_repo_list, repo_list_map = create_repo_list("/home/phatnt/code/github/HinnyCoder/retrieval/repos.txt")

    print(f'Number of repos: {len(encoded_repo_list)}')

    if (args.create_blank_databases):
        create_blank_databases(repo_list_map.keys())
    else:
        create_databases(repo_list_map.keys())

    embedding_model = model.hybrid.BGEM3EmbeddingFunction(model_name = 'BAAI/bge-m3', device = 'cuda:0', use_fp16 = False,)
    schemas = create_framework()
    
    for repo in encoded_repo_list:
        create_database(repo, schemas, embedding_model)
        break

if (__name__ == '__main__'):
    main()