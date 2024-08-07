import argparse
import logging
import multiprocessing
import os
import re
import subprocess
import sys
import warnings
from typing import List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{CWD}/..")
import dotenv
from make_data.run import get_functions, get_location
from tqdm import tqdm

dotenv.load_dotenv(f"{CWD}/.env", override=True)


class TestExecutor:
    def __init__(
        self,
        df: pd.DataFrame,
        column_to_check: str = "generated_code",
        proj_storage_dir: str = "",
        log_dir: str = "log_test",
        tool: str = "defects4j",
        index: int = 0,
    ):
        self.df = df
        self.column_to_check = column_to_check
        self.proj_storage_dir = proj_storage_dir
        self.log_dir = log_dir
        self.index = index
        self.logger = logging.getLogger(f"logger{self.index}")
        self.logger.addHandler(
            logging.FileHandler(f"{self.log_dir}/executor{self.index}.log")
        )
        self.logger.setLevel(logging.INFO)
        self.tool = tool

    def _fill_file(self, row: pd.Series) -> Optional[str]:
        absolute_file_path = "{}/{}/{}".format(
            self.proj_storage_dir, row["proj_name"], row["relative_path"]
        )
        with open(
            absolute_file_path, "r", encoding="utf-8", errors="ignore"
        ) as f:
            original_file = f.read().replace("\r\n", "\n")
        filled_class = row["masked_class"].replace(
            "<FILL_FUNCTION_BODY>", row[self.column_to_check]
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
                    filled_file = (
                        original_file[:class_start_idx]
                        + filled_class
                        + original_file[class_end_idx:]
                    )
                    return filled_file
            return None
        else:
            return None

    def _create_tmp_workdir(
        self,
        identifier: str,
        version: str,
        project_dir: str,
    ):
        if os.path.exists(project_dir):
            self.logger.info("\tAlready created tmp workspace")
            return
        try:
            cmd = f"""
            {self.tool} checkout -p {identifier} -v {version} -w {project_dir}
            """
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if os.path.exists(project_dir):
                self.logger.info("\tCreate tmp workspace successfully")
        except Exception:
            self.logger.error("\tCan not make tmp workspace")

    def _infilling_file(self, row, tmp_dir: str):
        # Replace filled file into original file
        try:
            filled_file = self._fill_file(row)
            if not filled_file:
                raise IOError("Can not fill file")
            infilling_file_url = f"{tmp_dir}/{row['relative_path']}"
            with open(
                infilling_file_url, "w", encoding="utf-8", errors="ignore"
            ) as f:
                f.write(filled_file)
            self.logger.info("\tFill file successfully")
        except Exception as e:
            self.logger.error("\tCan not fill file")

    def _test_feedback(self, project_dir: str, list_test: List[str]):
        # Run test
        try:
            cmd = f"""
            {self.tool} test -w {project_dir} -t {' '.join(list_test)}
            """
            res = subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            )
            self.logger.info(f"\t{res.stderr}")
            pattern = r"Failing tests: (\d+)"
            match = re.search(pattern, res.stdout)
            if match:
                test_failed = int(match.group(1))
                if test_failed == 0:
                    return "<success>"
                else:
                    return res.stdout
            else:
                return res.stderr
        except Exception:
            self.logger("\tCan not run test")

    def _execute(self, row):
        self.logger.info(
            f"Processing {row['proj_name']}/{row['relative_path']}:{row['func_name']}"
        )
        project = row["proj_name"].split("_")[1]
        tmp_dir = f"{os.environ.get('TMP_DIR')}/{row['task_id']}"
        self._create_tmp_workdir(
            identifier=row["project"],
            version=f"{str(row['bug_id'])}f",
            project_dir=f"{tmp_dir}/{project}",
        )

        self._infilling_file(row, tmp_dir=tmp_dir)

        feedback = self._test_feedback(
            project_dir=f"{tmp_dir}/{project}", list_test=row["testmethods"]
        )
        return feedback

    def execute(self):
        test_feedbacks = []
        counter = 0
        for _, row in tqdm(
            self.df.iterrows(),
            desc=f"Compiling",
            total=len(self.df),
            position=self.index,
        ):

            counter += 1
            test_feedbacks.append(self._execute(row))
            if counter % 10 == 0:
                log_df = self.df.iloc[:counter]
                log_df["test_feedback"] = test_feedbacks
                log_df.to_parquet(
                    f"{self.log_dir}/executor{self.index}.parquet"
                )
        return test_feedbacks


def process_dataframe(args):
    (df, column_to_check, proj_storage_dir, log_dir, tool, index) = args
    executor = TestExecutor(
        df, column_to_check, proj_storage_dir, log_dir, tool, index
    )

    test_feedbacks = executor.execute()
    df["test_feedback"] = test_feedbacks
    return df


def main(args):
    df = pd.read_parquet(args.input)
    dfs = np.array_split(df, args.proc)
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir, exist_ok=True)
    else:
        os.system(f"rm -rf {args.log_dir}/*")
    additional_args = (args.col, args.base_dir, args.log_dir, args.tool)
    list_args = []
    for i in range(len(dfs)):
        list_args.append((dfs[i],) + additional_args + (i,))

    with multiprocessing.Pool(args.proc) as p:
        results = p.map(process_dataframe, list_args)
    final_result = pd.concat(results, axis=0)
    print(
        "Pass test rate: {:.2f}".format(
            100
            * len(final_result[final_result["test_feedback"] == "<success>"])
            / len(final_result)
        )
    )
    final_result.to_parquet(args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--col", dest="col")
    parser.add_argument("--base-dir", dest="base_dir")
    parser.add_argument("--log-dir", dest="log_dir")
    parser.add_argument("--tool", dest="tool")
    parser.add_argument("--proc", dest="proc", type=int)
    args = parser.parse_args()
    main(args)
