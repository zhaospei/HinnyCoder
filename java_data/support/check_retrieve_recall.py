import pandas as pd
from tabulate import tabulate
import collections
from tqdm import tqdm
import json

df = pd.read_parquet("/home/thieuluu/HinnyCoder/java_data/data/rambo_sketch_output_with_retrieved_type_method.parquet")
actual = pd.read_parquet("/home/thieuluu/HinnyCoder/java_data/data/rambo_upperbound_rambo_re.parquet")

parsed = "/home/thieuluu/HinnyCoder/parsed_rambo"

res = []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Checking"):
    method_storage_url = f"{parsed}/{row['proj_name']}_methods.json"
    with open(method_storage_url, 'r') as f:
        methods = json.load(f)
    types = row["retrieved_type"]
    # if row["class_name"] in types:
    #     print(row)
    #     print("-" * 100)    # if row["class_name"] in types:
    #     print(row)
    #     print("-" * 100)
    all_methods = set()
    for method in methods:
        if method["class"] in types:
            all_methods.add(method["name"])
    
    all_methods.update(row["retrieved_method"])
    res.append({"relative_path": row["relative_path"],
                "potential_method_invoke": list(all_methods),
                "sketch_code_parsed_type": list(json.loads(row["type"])),
                "sketch_code_retrieved_type": list(row["retrieved_type"]),
                "sketch_code_parsed_method": list(json.loads(row["method"])),
                "sketch_code_retrieved_method": list(row["retrieved_method"]),
                "sketch_code": row["prediction"]})
    



has_method_invocation = 0
total_recall = 0
for _, row in tqdm(actual.iterrows(), total=len(actual), desc="Calculating"):
    for record in res:
        if record["relative_path"] == row["relative_path"]:
            record["actual_method_invoke"] = list(row["ground_truth.methods"])
            record["ground_truth"] = row["ground_truth"]
            if len(row["ground_truth.methods"]) == 0:
                record["recall"] = None
                continue

            has_method_invocation += 1
            recall = len(set(row["ground_truth.methods"]).intersection(set(record["potential_method_invoke"]))) / len(set(row["ground_truth.methods"]))
            total_recall += recall
            record["recall"] = recall

res = pd.DataFrame(res)
res.to_json("rambo_sketch_code_retrieved_methods.jsonl", orient="records", lines=True)

print("Mean recall: {:.2f}".format(total_recall / has_method_invocation * 100))
