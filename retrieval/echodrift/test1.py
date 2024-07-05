from pymilvus import connections, Collection, utility

connections.connect(alias="default", host="127.0.0.1", port="19530")
collection_name = "example_collection"
collection = Collection(name=collection_name)
collections = utility.list_collections()
print("Collections:", collections)
