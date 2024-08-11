import argparse
import logging
import os
from multiprocessing import Pool
from subprocess import run

import numpy as np
import pandas as pd
from tqdm import tqdm


def processor(args):
    projects, parser, base_dir, class_path, index, log_dir = args
    logger = logging.Logger(f"parse-project_{index}", logging.INFO)
    logger.addHandler(
        logging.FileHandler(f"{log_dir}/parse-project_{index}.log")
    )
    for project in tqdm(
        projects, total=len(projects), desc=f"Proc {index}", position=index
    ):
        cmd = (
            f"cd {parser}/target/classes "
            f"&& java -cp {class_path} "
            "Main "
            f"{base_dir} "
            f"{project}"
        )
        # print(cmd)
        # break
        try:
            result = run(cmd, shell=True, text=True, capture_output=True)
            logger.error(result.stderr)
        except Exception:
            print("<encounter_error>", project)


def main(args):
    df = pd.read_parquet(args.input)
    projects = df["proj_name"].unique().tolist()
    class_path = "." f":'{args.parser}/target/dependency/*'"
    parts = np.array_split(projects, args.num_proc)
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir, exist_ok=True)
    else:
        os.system(f"rm -rf {args.log_dir}/*")
    subsets = [
        (
            parts[i],
            args.parser,
            args.base_dir,
            class_path,
            i,
            args.log_dir,
        )
        for i in range(args.num_proc)
    ]
    with Pool(args.num_proc) as p:
        p.map(processor, subsets)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--parser", dest="parser")
    parser.add_argument("--base-dir", dest="base_dir")
    parser.add_argument("--num-proc", dest="num_proc", type=int)
    parser.add_argument("--log-dir", dest="log_dir")
    args = parser.parse_args()
    main(args)
