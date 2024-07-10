import argparse
import os
import re

import pandas as pd
from antlr4 import *
from tqdm import tqdm


def modify_modifier(code):
    while True:
        occurrence = re.search(r"\s(private\s)", code)
        if occurrence:
            start, end = occurrence.span(1)
            code = code[:start] + code[end:]
        else:
            break
    return code


# # Read the Java source file
# # with open('/data/hieuvd/lvdthieu/repos/tmp-projects/wkeyuan_DWSurvey/DWSurvey/src/main/java/net/diaowen/common/service/BaseServiceImpl.java', 'r') as file:
# with open(
#     # "/data/hieuvd/lvdthieu/repos/tmp-projects/classgraph_classgraph/classgraph/src/main/java/nonapi/io/github/classgraph/utils/Assert.java"
#     "/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/utils/InputSentence.java"
# ) as f:
#     java_code = f.read()

# # Extract class and method modifiers
# code, message = modify_modifiers(java_code)
# print(message)


# with open(
#     "/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/utils/ModifiedInputSentence.java",
#     "w",
# ) as f:
#     f.write(code)


def main(args):
    df = pd.read_parquet(args.input)
    for _, row in tqdm(
        df.iterrows(), total=len(df), desc="Modifying modifiers"
    ):
        path_to_file = f"{args.base_dir}/{row['proj_name']}/{row['relative_path']}"
        try:
            with open(path_to_file, "r") as f:
                code = f.read()
            new_code = modify_modifier(code)
            with open(path_to_file, "w") as f:
                f.write(new_code)
        except:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--log-dir", dest="log_dir")
    parser.add_argument("--base-dir", dest="base_dir")
    args = parser.parse_args()
    main(args)
