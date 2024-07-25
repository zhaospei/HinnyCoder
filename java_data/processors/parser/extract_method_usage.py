import argparse
import json

import pandas as pd


def main(args):
    df = pd.read_parquet(args.input)
    for i, row in df.iterrows():
        with open(f"{args.json_dir}/{row['proj_name']}_type.json") as f:
            project_types = json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("-col", dest="col")
    parser.add_argument("--json-dir", dest="json_dir")
    args = parser.parse_args()
    main(args)
