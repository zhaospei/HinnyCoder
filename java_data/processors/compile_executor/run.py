import argparse
import logging
import multiprocessing
import os
import re
import subprocess
from typing import List, Optional

import pandas as pd
from make_data.run import get_functions, get_location
from tqdm import tqdm


class CompilerExecutor:
    def __init__(
        self,
        df: pd.DataFrame = pd.DataFrame(),
        column_to_check: str = "generated_code",
        proj_storage_dir: str = "",
        log_dir: str = "/home/hieuvd/lvdthieu/log_compile",
        mvn: str = "",
        index: int = 0,
    ):
        """Constructor

        Args:
            df (pd.DataFrame): DataFrame that should include ["proj_name", "relative_path", "class_name", "func_name", column_to_check] columns
            column_to_check (str): Column name in df that need to check compilability
            proj_storage_dir (str): Where to store all projects
            log_dir (str): Where to store log information
            mvn (str): Runable maven file to compile java code
            index (int): Compiler index
        """
        self.df = df
        self.column_to_check = column_to_check
        self.proj_storage_dir = proj_storage_dir
        self.index = index
        self.logger = logging.getLogger(f"logger{self.index}")
        self.log_dir = log_dir
        self.logger.addHandler(
            logging.FileHandler(f"{self.log_dir}/compiler_{self.index}.log")
        )
        self.logger.setLevel(logging.INFO)
        self.mvn = mvn

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
                    return filled_file, original_file
            return None, None
        else:
            return None, None

    def _get_compiler_feedback(self, row):
        path_to_project = "{}/{}".format(
            self.proj_storage_dir, row["proj_name"]
        )
        cmd = (
            f"cd {path_to_project} "
            "&& cd $(ls -d */|head -n 1) "
            "&& echo $(pwd)"
            f"&& {self.mvn} clean compile -DskipTests -Dcheckstyle.skip -Dgpg.skip=true -Dlicense.skip=true"
        )
        data = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return data.stdout

    def _extract_error(self, compile_info: str):
        err_pattern = r"^\[ERROR\] (?P<file>.+?):\[(?P<line>\d+),(?P<col>\d+)\] (?P<err>.+)$"
        file_errors = []
        errors = set(re.findall(err_pattern, compile_info, re.MULTILINE))
        for error in errors:
            file, line, col, err = error
            file = file.replace(self.proj_storage_dir + "/", "")
            file_errors.append(
                f"""<file>{file}<line>{line}<col>{col}<err>{err}"""
            )
        return "\n".join(file_errors)

    def _execute(self, row: pd.Series) -> bool:
        self.logger.info(
            f"Processing {row['proj_name']}/{row['relative_path']}"
        )
        compiler_feedback = None

        try:
            filled_file, original_file = self._fill_file(row)
            if not filled_file:
                self.logger.error("\tCan not fill file")
                raise IOError("Can not fill file")
            else:
                self.logger.info("\tFilled file successfully")
                try:
                    path_to_file = "{}/{}/{}".format(
                        self.proj_storage_dir,
                        row["proj_name"],
                        row["relative_path"],
                    )
                    with open(
                        path_to_file, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        f.write(filled_file)
                    compile_info = self._get_compiler_feedback(row)
                    self.logger.info("\tGot compile info successfully")
                    compiler_feedback = self._extract_error(compile_info)
                    self.logger.info("\tExtracted error successfully")
                except:
                    self.logger.error("\tEncounter error while executing")
                    raise Exception("Encounter exception when executing")
                finally:
                    with open(
                        path_to_file, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        f.write(original_file)
                    self.logger.info("\tWrote back")
            if not compiler_feedback:
                compiler_feedback = "<success>"

        except Exception:
            compiler_feedback = "<execute_error>"

        return compiler_feedback

    def execute(self):
        compiler_feedbacks = []
        counter = 0
        for _, row in tqdm(
            self.df.iterrows(),
            desc=f"Proc {self.index}",
            total=len(self.df),
            position=self.index,
        ):
            counter += 1
            compiler_feedbacks.append(self._execute(row))
            if counter % 50 == 0:
                log_df = self.df.iloc[:counter]
                log_df["compiler_feedback"] = compiler_feedbacks
                log_df.to_parquet(
                    f"{self.log_dir}/executor{self.index}.parquet"
                )
        return compiler_feedbacks


def group_dataframes(df_list: List[pd.DataFrame], num_groups: int):
    """Group a list of DataFrames into a specified number of groups with roughly equal total rows.

    Args:
        df_list (List[pd.DataFrame]): List of DataFrames to be grouped.
        num_groups (int): Number of resulting groups.

    Returns:
        List[pd.DataFrame]: A list of grouped DataFrames.
    """
    # Initialize the groups
    groups = [[] for _ in range(num_groups)]
    group_sizes = [0] * num_groups

    # Sort DataFrames by size (optional, for better distribution)
    sorted_dfs = sorted(df_list, key=len, reverse=True)

    # Distribute DataFrames to groups
    for df in sorted_dfs:
        # Find the group with the smallest size
        min_group_index = group_sizes.index(min(group_sizes))

        # Add the DataFrame to this group
        groups[min_group_index].append(df)
        group_sizes[min_group_index] += len(df)

    # Concatenate the DataFrames within each group
    result_groups = [pd.concat(group, ignore_index=True) for group in groups]

    return result_groups


def process_dataframe(args):
    (df, column_to_check, proj_storage_dir, log_dir, mvn, index) = args
    compiler = CompilerExecutor(
        df, column_to_check, proj_storage_dir, log_dir, mvn, index
    )
    compiler_feedbacks = compiler.execute()
    df["compiler_feedback"] = compiler_feedbacks
    return df


def main(args):
    df = pd.read_parquet(args.input)
    proj_group = df.groupby(by="proj_name")
    dfs = [proj_group.get_group(x) for x in proj_group.groups]
    dfs = group_dataframes(dfs, args.proc)
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir, exist_ok=True)
    else:
        os.system(f"rm -rf {args.log_dir}/*")
    additional_args = (args.col, args.base_dir, args.log_dir, args.mvn)
    list_args = []
    for i in range(len(dfs)):
        list_args.append((dfs[i],) + additional_args + (i,))
    with multiprocessing.Pool(args.proc) as p:
        results = p.map(process_dataframe, list_args)
    final_result = pd.concat(results, axis=0)
    final_result.to_parquet(args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--col", dest="col")
    parser.add_argument("--base-dir", dest="base_dir")
    parser.add_argument("--log-dir", dest="log_dir")
    parser.add_argument("--mvn", dest="mvn")
    parser.add_argument("--proc", dest="proc", type=int)
    args = parser.parse_args()
    main(args)

