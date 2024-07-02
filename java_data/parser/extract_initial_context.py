# import argparse
# import os
# from multiprocessing import Pool, cpu_count
# from subprocess import run
# from typing import Callable, Optional

# import numpy as np
# import pandas as pd
# from tqdm import tqdm

# parser = argparse.ArgumentParser()
# parser.add_argument("--input", dest="input")
# parser.add_argument("--parser", dest="parser")
# parser.add_argument("--base-dir", dest="base_dir")
# parser.add_argument("--output", dest="output")
# parser.add_argument("--proc", dest="proc")
# parser.add_argument("--log-dir", dest="log_dir")
# BASE_DIR = os.path.dirname(os.path.realpath(__file__))


# # Define the processing function
# def process_chunk(args):
#     (index, df_chunk, parser, base_dir, class_path, log_dir) = args
#     relevant_context = []
#     counter = 0
#     for _, row in tqdm(
#         df_chunk.iterrows(),
#         total=len(df_chunk),
#         position=index,
#         desc=f"proc {index}",
#     ):
#         counter += 1
#         cmd = (
#             f"cd {parser}/target/classes "
#             f"&& java -cp {class_path} "
#             "Main "
#             f"{base_dir} "
#             f"{row['proj_name']} "
#             f"{row['relative_path']} "
#             f"{row['class_name']}"
#         )
#         try:
#             data = run(cmd, shell=True, text=True, capture_output=True)
#             relevant_context.append(data.stdout)
#         except:
#             relevant_context.append("<encounter_error>")

#         if counter % 50 == 0:
#             log_df = df_chunk.iloc[:counter]
#             log_df["relevant_context"] = relevant_context
#             log_df.to_parquet(f"{log_dir}/extracter{index}.parquet")
#     df_chunk["relevant_context"] = relevant_context
#     return df_chunk


# def parallelize_dataframe(
#     df: pd.DataFrame,
#     func: Callable,
#     parser: str,
#     base_dir: str,
#     class_path: str,
#     log_dir: str,
#     num_partitions: Optional[int] = None,
# ) -> pd.DataFrame:
#     if num_partitions is None:
#         num_partitions = cpu_count()

#     df_split = np.array_split(df, num_partitions)
#     with Pool(num_partitions) as pool:
#         tasks = [
#             (index, df_chunk, parser, base_dir, class_path, log_dir)
#             for index, df_chunk in enumerate(df_split)
#         ]
#         results = pool.map(func, tasks)

#     df = pd.concat(results)
#     return df


# def main(args):
#     dataset = pd.read_parquet(args.input)
#     class_path = "." f":'{args.parser}/target/dependency/*'"
#     dataset = parallelize_dataframe(
#         df=dataset,
#         func=process_chunk,
#         parser=args.parser,
#         base_dir=args.base_dir,
#         class_path=class_path,
#         log_dir=args.log_dir,
#         num_partitions=args.proc,
#     )
#     dataset.to_csv(args.output)


# if __name__ == "__main__":
#     args = parser.parse_args()
#     main(args)

import json
import logging
from multiprocessing import Pool
from subprocess import run
from typing import List, Optional

import pandas as pd
from tqdm import tqdm

project_storage_dir = "/data/hieuvd/lvdthieu/repos/processed-projects"
java_parser = "/home/hieuvd/lvdthieu/java-parser"
class_path = "." f":'{java_parser}/target/dependency/*'"
json_dir = "/home/hieuvd/lvdthieu/parsed_test"


def get_context(json_dir, project_name, qualified_name):
    with open(f"{json_dir}/{project_name}_type.json", "r") as f:
        types = json.load(f)

    for type in types:
        if type["qualified_name"] == qualified_name:
            return type["abstract"]
    return "<not_self_defined_class>"


def processor(args):
    df, project_storage_dir, json_dir, index = args
    logger = logging.Logger(f"extract_initial_context_{index}", logging.INFO)
    logger.addHandler(
        logging.FileHandler(
            f"/home/hieuvd/lvdthieu/extract_initial_context_{index}.log"
        )
    )
    initial_context = []
    cnt = 0
    for _, row in tqdm(
        df.iterrows(), total=len(df), desc=f"Proc {index}", position=index
    ):
        cmd = (
            f"cd {java_parser}/target/classes "
            f"&& java -cp {class_path} "
            "Main "
            f"{project_storage_dir} "
            f"{row['proj_name']} "
            f"{row['relative_path']} "
            f"{row['class_name']}"
        )
        try:
            result = run(cmd, shell=True, text=True, capture_output=True)
            output = result.stdout.strip()
            print(repr(output))
            match output:
                case (
                    "<encounter_error>"
                    | "<no_class>"
                    | "<cant_find_class>"
                    | "<cant_resolve_binding>"
                    | "<super_class_null>"
                ):
                    logger.error(
                        "{:<25} {:<40} {}".format(
                            output, row["proj_name"], row["relative_path"]
                        )
                    )
                    initial_context.append("<no_super_class>")
                case "<no_super_class>":
                    logger.info(
                        "{:<40} {} {}".format(
                            row["proj_name"],
                            row["relative_path"],
                            "has no super class",
                        )
                    )
                    initial_context.append("<no_super_class>")
                case _:
                    logger.info(
                        "{:<40} {} {}".format(
                            row["proj_name"],
                            row["relative_path"],
                            "has super class",
                        )
                    )
                    super_class_context = get_context(
                        json_dir,
                        row["proj_name"],
                        qualified_name=output,
                    )
                    initial_context.append(super_class_context)
        except:
            logger.error(
                "{:<25} {:<40} {}".format(
                    "<run_command>", row["proj_name"], row["relative_path"]
                )
            )
            initial_context.append("<error>")
        cnt += 1
        if cnt % 100 == 0:
            log_df = df.iloc[:cnt]
            log_df["initial_context"] = initial_context
            log_df.to_parquet(
                "/home/hieuvd/lvdthieu/log_extract_initial_context.parquet"
            )
    df["initial_context"] = initial_context
    return df


df = pd.read_parquet(
    "/home/hieuvd/lvdthieu/test_finetune_context_instruct.parquet"
)
new_df = processor((df, project_storage_dir, json_dir, 0))
new_df.to_parquet("/home/hieuvd/lvdthieu/initial_context.parquet")
