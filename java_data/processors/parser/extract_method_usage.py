import argparse
import json
import time
from functools import wraps
from typing import Tuple

import pandas as pd


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f"func:{func.__name__} took {total_time:.4f} sec")
        return result

    return timeit_wrapper


@timeit
def search_types(
    queries: str, json_file_url: str, except_file: str
) -> Tuple[str, str]:
    """Search type name in list of project self define types except type in except file

    Args:
        types (str): List of type name to search
        json_file_url (str): Where store list of project self define types
        except_file (str): Except file

    Returns:
        Tuple[str, str]: _description_
    """

    with open(json_file_url, "r") as f:
        types = json.load(f)
    result = [
        (type["name"], type["relative_path"])
        for query in queries
        for type in types
        if (query == type["name"] and type["relative_path"] != except_file)
    ]

    return result


@timeit
def search_methods(queries: Tuple[str, str], json_file_url: str):
    with open(json_file_url, "r") as f:
        methods = json.load(f)

    result = [
        method["name"]
        for (type_name, type_path) in queries
        for method in methods
        if (
            type_name == method["class"]
            and type_path == method["relative_path"]
        )
    ]

    return result


@timeit
def search_usages(queries: str, json_file_url: str):
    with open(json_file_url, "r") as f:
        methods = json.load(f)

    result = []
    for query in queries:
        for method in methods:
            method_invocation_pattern = f".{query}("
            if method_invocation_pattern in method["raw"]:
                result.append(f"Usage of {query}:\n{method['raw']}")
                break

    return "\n".join(result)


def main(args):
    df = pd.read_parquet(args.input)
    df = df.iloc[:10]
    retrieved_usages = []
    for _, row in df.iterrows():
        res_types = search_types(
            types=row[args.col],
            json_file_url=f"{args.json_dir}/{row['proj_name']}_types.json",
            except_file=f"{row['proj_name']}/{row['relative_path']}",
        )
        target_methods = search_methods(
            queries=res_types,
            json_file_url=f"{args.json_dir}/{row['proj_name']}_methods.json",
        )

        retrieved_usage = search_usages(
            queries=target_methods,
            json_file_url=f"{args.json_dir}/{row['proj_name']}_methods.json",
        )

        retrieved_usages.append(retrieved_usage)
    df["retrieval_usage"] = retrieved_usages
    df.to_parquet(args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("-col", dest="col")
    parser.add_argument("--json-dir", dest="json_dir")
    args = parser.parse_args()
    main(args)
