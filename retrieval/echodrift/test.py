from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection

# Connect to Milvus
connections.connect(alias="default", host="127.0.0.1", port="19530")

# Define the collection schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128)
]
schema = CollectionSchema(fields, "example collection")

# Create collection
collection_name = "example_collection"
collection = Collection(name=collection_name, schema=schema)

# Insert data
data = [
    [1, 2, 3],  # IDs
    [[0.1]*128, [0.2]*128, [0.3]*128]  # Vectors
]
collection.insert(data)

# Check if the collection exists
if utility.has_collection(collection_name):
    print(f"Collection '{collection_name}' exists.")
else:
    print(f"Collection '{collection_name}' does not exist.")

# List collections
collections = utility.list_collections()
print("Collections:", collections)
