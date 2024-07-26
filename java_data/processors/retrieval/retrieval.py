import argparse
import json
import re
import time
from functools import wraps
from typing import Optional, Tuple

import pandas as pd
from tqdm import tqdm


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


def search_repo(
    queries: str,
    json_file_url: str,
    except_file: str,
    topk: int = -1,
    threshold: Optional[float] = None,
) -> Tuple[str, str]:
    """Search `kind` (type or method) in list of project self define object
       except in `except file`

    Args:
        queries (str): List of queries to search
        json_file_url (str): Where store list of project self define types
        except_file (str): Except file
        kind (str): Choose from ['type', 'method']
        topk (int): If `topk` > 0 get maximum `topk` results for each query else
                    get max possible result
    Returns:
        Tuple[str, str]: _description_
    """

    with open(json_file_url, "r") as f:
        objects = json.load(f)
    if topk < 0:
        result = [
            obj
            for query in queries
            for obj in objects
            if (query == obj["name"] and obj["relative_path"] != except_file)
        ]
    else:
        result = []
        for query in queries:
            cnt = 0
            for obj in objects:
                if (
                    query == obj["name"]
                    and obj["relative_path"] != except_file
                ):
                    result.append(obj)
                    cnt += 1
                    if cnt == topk:
                        break
    return result


def search_method_invocations(queries: str, json_file_url: str):
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


def process_type(type: str):
    return re.findall(r"\b\w+\b", type)


def main(args):
    df = pd.read_parquet(args.input)
    retrieval = {
        "type_context": [],
        "type_context_no_cmt": [],
        "method_context": [],
        "type_method_usage": [],
        "sim_method_context": [],
    }
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Retrieving"):
        processed_types = [
            processed_type
            for type in row[args.type_col]
            for processed_type in process_type(type)
        ]
        res_types = search_repo(
            queries=processed_types,
            json_file_url=f"{args.json_dir}/{row['proj_name']}_types.json",
            except_file=f"{row['proj_name']}/{row['relative_path']}",
            k=1,
        )
        res_methods = search_repo(
            queries=row[args.method_col],
            json_file_url=f"{args.json_dir}/{row['proj_name']}_methods.json",
            except_file=f"{row['proj_name']}/{row['relative_path']}",
            k=1
        )
        type_context = "\n\n".join([type["abstract"] for type in res_types])
        type_context_no_cmt = "\n\n".join(
            [type["abstract_compact"] for type in res_types]
        )
        method_context = "\n\n".join([method["raw"] for method in res_methods])
        if not ("sim_method_context" in df.columns):
            similar_methods = search_repo(
                queries=[row[args.sim_col]],
                json_file_url=f"{args.json_dir}/{row['proj_name']}_methods.json",
                except_file=f"{row['proj_name']}/{row['relative_path']}",
                k=1,
            )
            sim_method_context = "\n\n".join(similar_methods)
            

    #     target_methods = search_methods(
    #         queries=res_types,
    #         json_file_url=f"{args.json_dir}/{row['proj_name']}_methods.json",
    #     )

    #     usage = search_usages(
    #        ries=target_method[]
    # s
    #   #         json_file_url=f"{args.json_dir}/{row['proj_name']}_methods.json",
    #     )

    #     retrieved_usages.append(retrieved_usage)
    # df["retrieval_usage"] = retrieved_usages
    # df.to_parquet(args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--type-col", dest="col")
    parser.add_argument("--method-col", dest="method_col")
    parser.add_argument("--sim-col", dest="sim_col")
    parser.add_argument("--json-dir", dest="json_dir")
    args = parser.parse_args()
    main(args)
