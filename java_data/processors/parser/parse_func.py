import logging
import os
from argparse import ArgumentParser
from subprocess import run
from typing import List, Optional

import pandas as pd
from make_data.run import get_functions, get_location
from tqdm import tqdm


def fill_file(
    row: pd.Series, project_storage_dir: str, generated_code_col: str
) -> Optional[List[str]]:
    path_to_file = (
        f"{project_storage_dir}/{row['proj_name']}/{row['relative_path']}"
    )

    with open(path_to_file, "r", encoding="utf-8", errors="ignore") as f:
        original_file = f.read().replace("\r\n", "\n")

    # candidates = row[generated_code_col].split("<candidate>")[:-1]
    candidates = [row[generated_code_col]]
    candidate_classes = []
    for candidate in candidates:
        candidate_classes.append(
            row["masked_class"].replace("<FILL_FUNCTION_BODY>", candidate)
        )
    # Find class in original file
    functions = get_functions(original_file)
    if functions:
        for function in functions:
            if (
                function["class_name"] == row["class_name"]
                and function["func_name"] == row["func_name"]
            ):
                class_start_idx, class_end_idx = get_location(
                    original_file, function["class_loc"]
                )
                filled_files = []
                for filled_class in candidate_classes:
                    filled_files.append(
                        (
                            original_file[:class_start_idx]
                            + filled_class
                            + original_file[class_end_idx:]
                        )
                    )
                return filled_files
        return None
    else:
        return None


def processor(args):
    (
        df,
        project_storage_dir,
        generated_code_col,
        parse_function,
        class_path,
        index,
        log_dir,
    ) = args
    logger = logging.Logger(f"parse-function_{index}", logging.INFO)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    else:
        os.system(f"rm -rf {log_dir}/*")
    logger.addHandler(
        logging.FileHandler(f"{log_dir}/parse-function_{index}.log")
    )
    retrieval_types = []
    retrieval_methods = []
    for _, row in tqdm(
        df.iterrows(), total=len(df), desc=f"Proc {index}", position=index
    ):
        filled_files = fill_file(row, project_storage_dir, generated_code_col)
        types = set()
        methods = set()

        for filled_file in filled_files:
            source_path = f"{parse_function}/tmp{index}.txt"
            with open(source_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(filled_file)
            method_name = row["func_name"]
            cmd = (
                f"cd {parse_function}/target/classes "
                f"&& java -cp {class_path} "
                "Main "
                f"{source_path} "
                f"{method_name}"
            )
            try:
                result = run(cmd, shell=True, text=True, capture_output=True)
                if result.returncode != 0:
                    logger.error(
                        f"<encounter_error> {row['proj_name']}/{row['relative_path']}"
                    )
                else:
                    elements = result.stdout.split("\n")[:-1]
                    if elements[0] == "<types>":
                        i = 1
                        while i < len(elements) and elements[i] != "<methods>":
                            types.add(elements[i])
                            i += 1
                        i += 1
                        while i < len(elements):
                            methods.add(elements[i])
                            i += 1
                
            except:
                logger.error(
                    f"<encounter_error> {row['proj_name']}/{row['relative_path']}"
                )
        retrieval_types.append(types)
        retrieval_methods.append(methods)
    df[f"{generated_code_col}_re_type"] = retrieval_types
    df[f"{generated_code_col}_re_method"] = retrieval_methods
    return df


def main(args):
    df = pd.read_parquet(args.input)
    class_path = "." f":'{args.parse_function}/target/dependency/*'"
    new_df = processor(
        (
            df,
            args.base_dir,
            args.generated_col,
            args.parse_function,
            class_path,
            0,
            args.log_dir,
        )
    )
    new_df.to_parquet(args.output)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--base-dir", dest="base_dir")
    parser.add_argument("--parse-function", dest="parse_function")
    parser.add_argument("--generated-col", dest="generated_col")
    parser.add_argument("--num-proc", dest="num_proc", type=int)
    parser.add_argument("--log-dir", dest="log_dir")
    args = parser.parse_args()
    main(args)
