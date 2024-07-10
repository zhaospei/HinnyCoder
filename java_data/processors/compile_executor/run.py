import argparse
import codecs
import logging
import os
import re
from multiprocessing import Process, Queue
from subprocess import run
from typing import Optional

import pandas as pd
from make_data.make_data import get_functions, get_location
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--input", dest="input")
parser.add_argument("--output", dest="output")
parser.add_argument("--col", dest="col")
parser.add_argument("--base-dir", dest="base_dir")
parser.add_argument("--log-dir", dest="log_dir")
parser.add_argument("--mvn", dest="mvn")
parser.add_argument("--proc", dest="proc", type=int)
parser.add_argument("--start-end", dest="start_end")


class CompilerExecutor:
    def __init__(
        self,
        df: pd.DataFrame,
        column_to_check: str,
        proj_storage_dir: str,
        log_dir: str,
        mvn: str,
        index: int,
    ):
        """Constructor
        Args:
            df (pd.DataFrame): Dataframe of java code
            column_to_check (str): Column to check
            proj_storage_dir (str): Project storage directory
            output (str): Output
            index (int): Order of this executor
        """
        self.df = df
        self.column_to_check = column_to_check
        self.proj_storage_dir = proj_storage_dir
        self.logger = logging.getLogger(f"logger{self.index}")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        else:
            os.system(f"rm -rf {log_dir}/*")
        self.logger.addHandler(
            logging.FileHandler(f"{log_dir}/compile_{self.index}.log")
        )
        self.mvn = mvn
        self.index = index

    def _fill_file(self, row) -> Optional[str]:
        """Fill generated code to file
        Args:
            row (pd.core.series.Series): Row
            generated_func_column (str): Generated function column
            project_storage_url (str): Project storage url

        Returns:
            str: Filled generated code to file, if None, there is an error while filling file
        """
        absolute_file_path = "{}/{}/{}".format(
            self.proj_storage_dir, row["proj_name"], row["relative_path"]
        )
        with codecs.open(
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

    def _execute(self, row) -> bool:
        """Replace original file with file with generated code"""
        path_to_file = "{}/{}/{}".format(
            self.proj_storage_dir, row["proj_name"], row["relative_path"]
        )
        self.logger.info(
            f"Processing {row['proj_name']}/{row['relative_path']}"
        )
        compiler_feedback = None
        # If fail log file path into error file
        try:
            filled_file, original_file = self._fill_file(row)
            if not filled_file:
                self.logger.error("\tCan not fill file")
                raise IOError(
                    "There is an error while filling file {}".format(
                        path_to_file
                    )
                )
            else:
                self.logger.info("\tFill file successfully")
                try:
                    with codecs.open(
                        path_to_file, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        f.write(filled_file)

                    compile_info = self._get_compiler_feedback(row)
                    self.logger.info("\tGet compile info successfully")
                    compiler_feedback = self._extract_error(compile_info)
                    self.logger.info("\tExtract error successfully")
                except:
                    self.logger.error("\tEncounter error while executing")
                    raise Exception("Encounter exception when executing")
                finally:
                    with codecs.open(
                        path_to_file, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        f.write(original_file)
                    self.logger.info("\tWrote back")
            if not compiler_feedback:
                compiler_feedback = "<success>"

        except Exception:
            compiler_feedback = "<execute_error>"

        return compiler_feedback

    def _extract_error(self, compile_info):
        """Extract error from feedback
        Args:
            compile_info (List[CompilerFeedback]): Compiler feedback
        Returns:
            Dict[FileInfo, ErrorInfo]: Error info
        """
        # lines = filled_file.splitlines()
        err_pattern = r"^\[ERROR\] (?P<file>.+?):\[(?P<line>\d+),(?P<col>\d+)\] (?P<err>.+)$"
        file_errors = []
        errors = set(re.findall(err_pattern, compile_info, re.MULTILINE))
        for error in errors:
            file, line, col, err = error

            file_errors.append(
                f"""<file>{file}<line>{line}<col>{col}<err>{err}"""
            )
        return "\n".join(file_errors)

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
        data = run(cmd, shell=True, capture_output=True, text=True)
        return data.stdout

    def execute(self):
        compiler_feedbacks = []
        counter = 0
        for _, row in tqdm(
            self.df.iterrows(),
            desc=f"proc {self.index}",
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


def group_dataframes(df_list, num_groups):
    """Group a list of DataFrames into a specified number of groups with roughly equal total rows.

    Args:
        df_list (List[pd.DataFrame]): List of DataFrames to be grouped.
        num_groups (int): Number of resulting groups.

    Returns:
        List[pd.DataFrame]: A list of grouped DataFrames.
    """
    # Calculate the total number of rows
    total_rows = sum(len(df) for df in df_list)

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


def process_dataframes_in_parallel(df_list, additional_args, process_dataframe):
    """
    Process multiple DataFrames in parallel.

    Args:
        df_list (list of pd.DataFrame): List of DataFrames to process.

    Returns:
        List of results from processing each DataFrame.
    """
    processes = []
    output_queue = Queue()

    # Create a process for each DataFrame
    for idx, df in enumerate(df_list):
        p = Process(
            target=process_dataframe,
            args=(df, additional_args + (idx,), output_queue),
        )
        processes.append(p)
        p.start()
    # Collect the results
    results = []
    for _ in df_list:
        results.append(output_queue.get())
    # Ensure all processes have finished
    for p in processes:
        p.join()

    return results


def process_dataframe(df, additional_args, output_queue):
    """
    Process a DataFrame and put the result in the output queue.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        output_queue (Queue): The queue to store the results.
    """
    (col, base_dir, log_dir, mvn, index) = additional_args
    # Example processing: here we just return the DataFrame size
    executor = CompilerExecutor(df, col, base_dir, log_dir, mvn, index)
    df["compiler_feedback"] = executor.execute()
    output_queue.put(df)


def main(args):
    df = pd.read_parquet(args.input)
    proj_group = df.groupby(by="proj_name")
    dfs = [proj_group.get_group(x) for x in proj_group.groups]
    dfs = group_dataframes(dfs, args.proc)
    additional_args = (
        args.col,
        args.base_dir,
        args.log_dir,
        args.mvn,
    )
    start, end = map(int, args.start_end.split(":"))
    results = process_dataframes_in_parallel(
        dfs[start:end], additional_args, process_dataframe
    )
    final_result = pd.concat(results, axis=0)
    final_result.to_parquet(args.output)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
