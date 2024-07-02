import logging
from multiprocessing import Pool
from subprocess import run
from typing import List, Optional

import pandas as pd
from make_data.make_data import get_functions, get_location
from tqdm import tqdm
import re

base_dir = "/data/hieuvd/lvdthieu/repos/processed-projects"
parse_function = "/home/hieuvd/lvdthieu/parse_function"
class_path = "." f":'{parse_function}/target/dependency/*'"


def fill_file(
    row, project_storage_dir, generated_code_col
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

def extract_list(input_string, category):
    pattern = rf"{category}: \[(.*?)\]"
    match = re.search(pattern, input_string)
    if match:
        list_content = match.group(1)
        return [item.strip() for item in list_content.split(',')]
    return []

def processor(args):
    df, project_storage_dir, generated_code_col, index = args
    logger = logging.Logger(f"parse-function_{index}", logging.INFO)
    logger.addHandler(
        logging.FileHandler(f"/home/hieuvd/lvdthieu/parse-function_{index}.log")
    )
    retrieval_elements = []
    for _, row in tqdm(
        df.iterrows(), total=len(df), desc=f"Proc {index}", position=index
    ): 
        filled_files = fill_file(row, project_storage_dir, generated_code_col)
        types = set()
        methods = set()
        fields = set()
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
                types.update(extract_list(result.stdout, "Types"))
                methods.update(extract_list(result.stdout, "Methods"))
                fields.update(extract_list(result.stdout, "Fields")) 
            except:
                logger.error(f"<encounter_error> {row['relative_path']}")
        retrieval_element = {
            "types": types,
            "methods": methods,
            "fields": fields
        }

        retrieval_elements.append(retrieval_element)
    df["retrieval_element"] = retrieval_elements
    return df

df = pd.read_parquet(
    "/home/hieuvd/lvdthieu/deepseek_test_initial_context_output.parquet"
)
new_df = processor((df, base_dir, "initial_output", 0))
new_df.to_parquet("/home/hieuvd/lvdthieu/retrieval_element_test.parquet")