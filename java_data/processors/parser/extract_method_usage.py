import argparse
import pandas as pd
import json

def main(args):
    df = pd.read_parquet(args.input)
    
    # for i, row in df.iterrows():
    #     types = []
    #     for dic in json.loads(df.loc[i, args.retrieved_col]).get("types", []):
    #         types.extend(dic.values())
    #     with open(f"{args.json_dir}/{row['proj_name']}_type.json") as f:
    #         project_types = json.load(f)
    #     for type in types:
    #         for project_type in project_types:
    #             if type == project_type["name"]:


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--retrieved-col", dest="type_col")
    parser.add_argument("--json-dir", dest="json_dir")
    args = parser.parse_args()
    main(args)