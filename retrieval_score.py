import argparse
import collections
import json

import numpy as np
import pandas as pd
from tqdm import tqdm


def recall_type(args):
    df = pd.read_parquet(args.input)
    ground_truth = []
    max_len = 0
    for _, row in tqdm(df.iterrows(), total=len(df)):
        gt_type_in_project = []
        with open(f"{args.json_dir}/{row['proj_name']}_type.json") as f:
            project_types = json.load(f)
        for gt_type in row[args.gt_col]:
            for project_type in project_types:
                if gt_type == project_type["name"]:
                    gt_type_in_project.append(gt_type)
                    break
        if max_len < len(gt_type_in_project):
            max_len = len(gt_type_in_project)
        ground_truth.append(gt_type_in_project)

    gt_distribution = dict(collections.Counter(map(len, ground_truth)))
    num_type = range(max_len + 1)
    percentage = [
        "{:.3f}".format(gt_distribution.get(i, 0) / len(df))
        for i in range(max_len + 1)
    ]
    print("Ground truth distribution:")
    print(
        pd.DataFrame(
            {"Num type": num_type, "Percentage": percentage}
        ).to_markdown()
    )
    re_recalls = [
        len(set(df.loc[i, args.re_col]) & set(ground_truth[i]))
        / len(set(ground_truth[i]))
        for i in range(len(df))
        if len(set(ground_truth[i])) != 0
    ]
    print("Parse Draft Code Recall:")
    print("{:.2f}".format(np.mean(re_recalls) * 100))

    retrieved_types = []
    for i in range(len(df)):
        types = []
        for dic in json.loads(df.loc[i, args.retrieved_col]).get("types", []):
            types.extend(dic.values())
        retrieved_types.append(types)
    retrieved_recalls = [
        len(set(retrieved_types[i]) & set(ground_truth[i]))
        / len(set(ground_truth[i]))
        for i in range(len(df))
        if len(set(ground_truth[i])) != 0
    ]
    print("Retrieved Recall:")
    print("{:.2f}".format(np.mean(retrieved_recalls) * 100))


def recall_method(args):
    df = pd.read_parquet(args.input)
    ground_truth = []
    max_len = 0
    for _, row in tqdm(df.iterrows(), total=len(df)):
        gt_method_in_project = []
        with open(f"{args.json_dir}/{row['proj_name']}_methods.json") as f:
            project_methods = json.load(f)
        for gt_method in row[args.gt_col]:
            for project_type in project_methods:
                if gt_method == project_type["name"]:
                    gt_method_in_project.append(gt_method)
                    break
        if max_len < len(gt_method_in_project):
            max_len = len(gt_method_in_project)
        ground_truth.append(gt_method_in_project)

    gt_distribution = dict(collections.Counter(map(len, ground_truth)))
    num_method = range(max_len + 1)
    percentage = [
        "{:.3f}".format(gt_distribution.get(i, 0) / len(df))
        for i in range(max_len + 1)
    ]
    print("Ground truth distribution:")
    print(
        pd.DataFrame(
            {"Num method": num_method, "Percentage": percentage}
        ).to_markdown()
    )
    re_recalls = [
        len(set(df.loc[i, args.re_col]) & set(ground_truth[i]))
        / len(set(ground_truth[i]))
        for i in range(len(df))
        if len(set(ground_truth[i])) != 0
    ]
    print("Parse Draft Code Recall:")
    print("{:.2f}".format(np.mean(re_recalls) * 100))

    retrieved_methods = []
    for i in range(len(df)):
        methods = []
        for dic in json.loads(df.loc[i, args.retrieved_col]).get("methods", []):
            methods.extend(dic.values())
        retrieved_methods.append(methods)
    retrieved_recalls = [
        len(set(retrieved_methods[i]) & set(ground_truth[i]))
        / len(set(ground_truth[i]))
        for i in range(len(df))
        if len(set(ground_truth[i])) != 0
    ]
    print("Retrieved Recall:")
    print("{:.2f}".format(np.mean(retrieved_recalls) * 100))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument(
        "--json-dir",
        dest="json_dir",
        default="/home/hieuvd/lvdthieu/HinnyCoder/java_data/parse_project/target/classes",
    )
    parser.add_argument("--gt-col", dest="gt_col", default="func_body_re_type")
    parser.add_argument(
        "--re-col", dest="re_col", default="param_class_output_re_type"
    )
    parser.add_argument(
        "--retrieved-col", dest="retrieved_col", default="retrieved_names"
    )
    parser.add_argument("--task", dest="task", choices=["type", "method"])
    args = parser.parse_args()
    if args.task == "type":
        recall_type(args)
    else:
        recall_method(args)
