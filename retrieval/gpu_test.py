from pymilvus import MilvusClient, DataType, model, connections, db
from threading import Thread
from tqdm import tqdm
import argparse
import json

uri = 'http://localhost:19530'
data_prefix = 'data'
raw_prefix = f'{data_prefix}/raw'
db_prefix = f'{data_prefix}/database'

connections.connect(host = '127.0.0.1', port = 19530)

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

# create a repo_list and hash it for database name
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

# create a schema for types
def create_types_schema():
    schema = MilvusClient.create_schema(
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
    schema.add_field(field_name = 'abstract', datatype = DataType.VARCHAR, max_length = 65535)
    schema.add_field(field_name = 'raw', datatype = DataType.VARCHAR, max_length = 65535)

    # schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

# create a schema for methods
def create_methods_schema():
    schema = MilvusClient.create_schema(
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

    # schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

# create a schema for fields
def create_fields_schema():
    schema = MilvusClient.create_schema(
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

    # schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 65535)

    return schema

# create a generic schema
def create_generic_schema():
    schema = MilvusClient.create_schema(
        auto_id = False,
        enable_dynamic_fields = True,
    )

    schema.add_field(field_name = 'id', datatype = DataType.INT64, is_primary = True)
    schema.add_field(field_name = 'vector', datatype = DataType.FLOAT_VECTOR, dim = 1024)
    schema.add_field(field_name = 'name', datatype = DataType.VARCHAR, max_length = 5000)
    schema.add_field(field_name = 'data_path', datatype = DataType.VARCHAR, max_length = 5000)

    return schema

def create_framework():
    default_schema = create_generic_schema()

    schemas = {
        'types': default_schema,
        'methods': default_schema,
    }

    return schemas

# insert data into database, multithreading
class insert_data_by_thread(Thread):
    def __init__(self, client, repo, dt, embedding_model):
        Thread.__init__(self)
        self.client = client
        self.repo = repo
        self.dt = dt
        self.embedding_model = embedding_model
        self.data_dir = f'{raw_prefix}/{repo}_{dt}.json'
        print(self.data_dir)

    def run(self):
        data_dir = self.data_dir
        embedding_model = self.embedding_model

        f = open(data_dir)
        datas = json.load(f)
        f.close()

        names = [data['name'] for data in datas]
        vector_embeddings = embedding_model.encode_documents(names)
        dense_vectors = vector_embeddings['dense']

        for i in tqdm(range(len(datas)), desc = f'{self.repo}_{self.dt}'):
            inserted_data = {}
            inserted_data['id'] = i
            inserted_data['name'] = names[i]
            inserted_data['vector'] = dense_vectors[i]
            inserted_data['data_path'] = data_dir

            self.client.insert(
                collection_name = self.dt,
                data = inserted_data,
            )

def insert_data(client, repo, dt, embedding_model):
    data_dir = f'{raw_prefix}/{repo}_{dt}.json'

    embedding_model = embedding_model

    f = open(data_dir)
    datas = json.load(f)
    f.close()

    names = [data['name'] for data in datas]
    vector_embeddings = embedding_model.encode_documents(names)
    dense_vectors = vector_embeddings['dense']

    inserted_datas = []

    for i in tqdm(range(len(datas)), desc = f'{repo}_{dt}'):
        inserted_data = {}
        inserted_data['id'] = i
        inserted_data['name'] = names[i]
        inserted_data['vector'] = dense_vectors[i]
        inserted_data['data_path'] = data_dir

        inserted_datas.append(inserted_data)

    client.upsert(
        collection_name = dt,
        data = inserted_datas,
    )

def create_database(encoded_repo, schemas, embedding_model):
    print(encoded_repo['repo'])

    try:
        client = MilvusClient(
            uri = uri,
            db_name = encoded_repo['hashed_repo'],
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

        data_type = ['types']

        for dt in data_type:
            if client.has_collection(collection_name = dt):
                client.drop_collection(collection_name = dt)

            client.create_collection(
                collection_name = dt,
                schema = schemas[dt],
            )

            client.create_index(
                collection_name = dt,
                index_params = index_params,
            )

        for dt in data_type:
            insert_data(client, encoded_repo['repo'], dt, embedding_model)

        # pool = []
        # for dt in data_type:
        #     inserter = insert_data_by_thread(client, encoded_repo['repo'], dt, embedding_model)
        #     pool.append(inserter)

        # for inserter in pool:
        #     inserter.start()

        # for inserter in pool:
        #     inserter.join()

        client.close()
    except Exception as e:
        with open('logs.txt', 'a') as f:
            print(f'error occured at {encoded_repo["repo"]}')
            f.write(encoded_repo['repo'] + '\n')

    print('-' * 50)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--create_blank_databases',
        action = 'store_true',
        help = 'create blank databases'
    )

    parser.add_argument(
        '--scan_databases',
        action = 'store_true',
        help = 'scan for new databases'
    )

    args = parser.parse_args()

    scan_db = False
    if (args.scan_databases):
        scan_db = True

    encoded_repo_list, repo_list_map = create_repo_list(scan_db)

    print(f'number of repos: {len(encoded_repo_list)}')

    if (args.create_blank_databases):
        create_blank_databases([repo_list_map[i] for i in repo_list_map])
    else:
        create_databases([repo['hashed_repo'] for repo in encoded_repo_list])

    embedding_model = model.hybrid.BGEM3EmbeddingFunction(model_name = 'BAAI/bge-m3', device = 'cuda:0', use_fp16 = False,)
    schemas = create_framework()

    cnt = 0
    db_list = db.list_database()
    for repo in encoded_repo_list:
        # if ((not args.create_blank_databases) and (repo['hashed_repo'] in db_list)):
        #     continue

        client = MilvusClient(
            uri = uri,
            db_name = repo['hashed_repo'],
        )

        # if (len(client.list_collections()) > 0):
        #     client.close()

        #     continue

        create_database(repo, schemas, embedding_model)

        client.close()

        cnt += 1

        # if (cnt == 1):
        #     break

if (__name__ == '__main__'):
    main()