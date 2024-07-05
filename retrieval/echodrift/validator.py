# from pymilvus import MilvusClient, connections, Collection
# uri = 'http://localhost:19530'

# from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection

# # Connect to Milvus
# connections.connect("default", host="localhost", port="19530")

# # Create MilvusClient class to manage database and collection interactions
# class MilvusClient:
#     def __init__(self, alias, db_name):
#         self.alias = alias
#         self.db_name = db_name
#         # Connect to a specific database using the alias
#         connections.connect(alias=self.alias, db_name=self.db_name)

#     def get_num_entities(self, collection_name):
#         collection = Collection(name=collection_name)
#         return collection.num_entities


# def create_repo_list(repos_storage: str):
#     with open(repos_storage, 'r') as f:
#         repo_list = list(map(lambda line: line.strip(), f.readlines()))
#     import hashlib
#     encoded_repo_list = [
#         {
#             'repo': repo,
#             'hashed_repo': f'db_{hashlib.sha256(repo.encode("utf-8")).hexdigest()}',
#         }
#         for repo in repo_list
#     ]
#     repo_list_map = {}
#     for repo in encoded_repo_list:
#         repo_list_map[repo['hashed_repo']] = repo['repo']
#     return encoded_repo_list, repo_list_map


# def validate(encoded_repo):
#     client = MilvusClient(alias="default", db_name=encoded_repo["hashed_repo"])
#     print(client.get_num_entities("types"))

# if __name__ == "__main__":
#     encoded_repo_list, repo_list_map = create_repo_list("/home/phatnt/code/github/HinnyCoder/retrieval/repos.txt")
#     for encoded_repo in encoded_repo_list:
#         validate(encoded_repo)
#         break
from pymilvus import list_collections, connections


connections.connect(alias="default", host="127.0.0.1", port="19530")

# List all collections
collections = list_collections()
print("Collections:", collections)


