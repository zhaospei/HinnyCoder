import argparse
import os
from multiprocessing import Pool, cpu_count
from subprocess import run
from typing import Callable, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--input", dest="input")
parser.add_argument("--parser", dest="parser")
parser.add_argument("--base-dir", dest="base_dir")
parser.add_argument("--output", dest="output")
parser.add_argument("--proc", dest="proc")
parser.add_argument("--log-dir", dest="log_dir")
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


# Define the processing function
def process_chunk(args):
    (index, df_chunk, parser, base_dir, class_path, log_dir) = args
    relevant_context = []
    counter = 0
    for _, row in tqdm(
        df_chunk.iterrows(),
        total=len(df_chunk),
        position=index,
        desc=f"proc {index}",
    ):
        counter += 1
        cmd = (
            f"cd {parser}/target/classes "
            f"&& java -cp {class_path} "
            "Main "
            f"{base_dir} "
            f"{row['proj_name']} "
            f"{row['relative_path']} "
            f"{row['class_name']}"
        )
        try:
            data = run(cmd, shell=True, text=True, capture_output=True)
            relevant_context.append(data.stdout)
        except:
            relevant_context.append("<encounter_error>")

        if counter % 50 == 0:
            log_df = df_chunk.iloc[:counter]
            log_df["relevant_context"] = relevant_context
            log_df.to_parquet(f"{log_dir}/extracter{index}.parquet")
    df_chunk["relevant_context"] = relevant_context
    return df_chunk


def parallelize_dataframe(
    df: pd.DataFrame,
    func: Callable,
    parser: str,
    base_dir: str,
    class_path: str,
    log_dir: str,
    num_partitions: Optional[int] = None,
) -> pd.DataFrame:
    if num_partitions is None:
        num_partitions = cpu_count()

    df_split = np.array_split(df, num_partitions)
    with Pool(num_partitions) as pool:
        tasks = [
            (index, df_chunk, parser, base_dir, class_path, log_dir)
            for index, df_chunk in enumerate(df_split)
        ]
        results = pool.map(func, tasks)

    df = pd.concat(results)
    return df


def main(args):
    dataset = pd.read_parquet(args.input)
    class_path = "." f":'{args.parser}/target/dependency/*'"
    dataset = parallelize_dataframe(
        df=dataset,
        func=process_chunk,
        parser=args.parser,
        base_dir=args.base_dir,
        class_path=class_path,
        log_dir=args.log_dir,
        num_partitions=args.proc,
    )
    dataset.to_csv(args.output)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
