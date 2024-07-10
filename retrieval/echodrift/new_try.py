from pymilvus import MilvusClient, model, FieldSchema, DataType, CollectionSchema
import json
from tqdm import tqdm


data_raw = "/home/phatnt/code/github/HinnyCoder/retrieval/data/raw"
database = "/home/phatnt/code/github/HinnyCoder/retrieval/data/database"


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


def create_database(encoded_repo: str, scheme, embedding_model):
    try:
        hashed_repo = encoded_repo["hashed_repo"]
        repo = encoded_repo["repo"]
        print("Processing:", repo)
        client = MilvusClient(
            db_name = f"{database}/{hashed_repo}.db",
        )
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name = 'vector',
            metric_type = "L2",
            index_type = "GPU_IVF_FLAT",
            params = {
                'nlist': 1024,
            },
        )
        if client.has_collection(collection_name = "types"):
            client.drop_collection(collection_name = "types")

        client.create_collection(
            collection_name = "types",
            schema = schema,
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
            insert_data = {
                'id': i,
                'name': names[i],
                'vector': dense_vectors[i],
                'data_path': repo_info_url
            }
            client.insert(collection_name="types", data=insert_data,)
        
        client.load_collection(collection_name="types")
        res = client.query(collection_name="types", output_fields=["count(*)"])
        print(res)
        print(type(res))
        client.release_collection(collection_name="types")
        client.close()
    except Exception as e:
        pass
    

if __name__ == "__main__":
    encoded_repo_list, repo_list_map = create_repo_list("/home/phatnt/code/github/HinnyCoder/retrieval/repos.txt")
    embedding_model = model.hybrid.BGEM3EmbeddingFunction(model_name = 'BAAI/bge-m3', device = 'cuda:0', use_fp16 = False,)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
        FieldSchema(name="data_path", dtype=DataType.VARCHAR, max_length=255)
    ]
    schema = CollectionSchema(fields, "types") 
    for encoded_repo in encoded_repo_list:
        create_database(encoded_repo, schema, embedding_model)
        break

