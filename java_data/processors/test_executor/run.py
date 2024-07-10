"""Test executor
"""

import argparse
import pprint
import subprocess
from multiprocessing import Pool
from typing import List, Optional, Tuple

import pandas as pd
from make_data.make_data import get_functions, get_location
from tqdm import tqdm

pp = pprint.PrettyPrinter(depth=4, indent=4)

class TestExecutor:
    """Test Executor
    Args:
        dataframe (pd.DataFrame): Dataframe of test info
        column_to_check (str): Column to check
        project_storage_dir (str): Project storage directory
        output (str): Output
        index (int): Order of this executor
    """

    def __init__(
        self,
        df: pd.DataFrame,
        column_to_check: str,
        project_storage_dir: str,
        test_dir: str,
        log_dir: str,
        index: int,
        mvn: str,
        clover_jar: str,
        junit_jar: str,
        hamcrest_jar: str,
        separator_code: str,
    ):
        self.df = df
        self.column_to_check = column_to_check
        self.project_storage_dir = project_storage_dir
        self.test_dir = test_dir
        self.log_dir = log_dir
        self.index = index
        self.mvn = mvn
        self.clover_jar = clover_jar
        self.junit_jar = junit_jar
        self.hamcrest_jar = hamcrest_jar
        self.separator_code = separator_code

    def get_original_file(self, row) -> str:
        """
        Get the original file content for a given row.

        Args:
            row (dict): The row containing the project name and relative path.

        Returns:
            str: The content of the original file with newline characters replaced.
        """
        path_to_file = f"{self.project_storage_dir}/{row['proj_name']}/{row['relative_path']}"

        with open(path_to_file, "r", encoding="utf-8", errors="ignore") as f:
            original_file = f.read().replace("\r\n", "\n")

        return original_file

    def fill_file(self, row) -> Optional[str]:
        """
        Fills the content of a file with the given row's masked class
        and the content of the column specified by `self.column_to_check`.

        Args:
            row (dict): A dictionary containing the following keys:
                - 'masked_class' (str): The masked class to be replaced in the file.
                - 'class_name' (str): The name of the class to be filled.
                - 'func_name' (str): The name of the function to be filled.
                - 'relative_path' (str): The relative path to the file.
                - 'proj_name' (str): The name of the project.
                - The value of the column specified by `self.column_to_check`.

        Returns:
            str or None: The filled file content if the class and function are found
            in the file, or None otherwise.
        """
        original_file = self.get_original_file(row)
        filled_class = row["masked_class"].replace(
            "<FILL_FUNCTION_BODY>", row[self.column_to_check]
        )
        # print("original_file:", original_file)
        functions = get_functions(original_file)
        # print("functions:", functions)
        if not functions:
            return None, None

        for function in functions:
            # print("function:", function)
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
                # print("filled_file:", filled_file)
                return filled_file, original_file

        return None, None

    def get_test_info(self, row) -> Tuple[str, str]:
        src = (
            f"{self.project_storage_dir}/{row['proj_name']}/"
            f"{row['relative_path'].split('/src/main/java/')[0] + '/src'}"
        )
        test_dir = (
            f"{self.test_dir}/{row['proj_name']}/"
            f"{row['relative_path'].replace('.java', '')}"
        )
        db = f"{test_dir}/clover.db"
        instr = f"{test_dir}/build/instr"
        bin = f"{test_dir}/bin"
        test_java = f"{test_dir}/RegressionTest0.java"
        test_java_pass = f"{test_dir}/RegressionPassTest0.java"
        test_java_fail = f"{test_dir}/RegressionFailTest0.java"
        classpath = f"{test_dir}/classpath.txt"
        source = f"{test_dir}/sources.txt"
        test_result = f"{test_dir}/test_result.txt"
        pass_result = f"{test_dir}/clover_html_pass"
        fail_result = f"{test_dir}/clover_html_fail"

        cmd = f"""
            # Clear clover.db
            cd {test_dir} && rm -rf clover.db*

            # Instrument
            java -cp {self.clover_jar} com.atlassian.clover.CloverInstr -i {db} -s {src} -d {instr}
            if [ "$?" -eq 0 ]; then
                echo "1) Instrument done"
            else
                exit 1
            fi

            # Collect all dependence class path
            # Find all source file in src folder
            # Compile instrument files
            cd {src}/.. && {self.mvn} dependency:build-classpath -Dmdep.outputFile={classpath} && find {instr} -name "*.java" >{source} && javac -cp $(cat {classpath}):{self.clover_jar}:{instr} -d {bin} @{source}
            if [ "$?" -eq 0 ]; then
                echo "2) Compile instrumented code done"
            else
                exit 2
            fi

            # Compile test file
            javac -cp {bin}:{self.junit_jar}:{self.hamcrest_jar} {test_java} -d {bin}
            if [ "$?" -eq 0 ]; then
                echo "3) Compile test done"
            else
                exit 3
            fi

            # Run test
            cd {bin} && java -cp .:{self.clover_jar}:{self.junit_jar}:{self.hamcrest_jar} org.junit.runner.JUnitCore RegressionTest0 > {test_result}
            if [ "$?" -eq 0 ]; then
                echo "4) Run test done"
            else
                echo exit 4
            fi
            # Remove clover.db...
            cd {test_dir} && rm -rf clover.db[!.]*
            if [ "$?" -eq 0 ]; then
                echo "5) Remove tmp clover.db done"
            else
                exit 5
            fi
            # Generate pass and fail test
            python {self.separator_code} \
                --result {test_result} \
                --all {test_java} \
                --pass {test_java_pass} \
                --fail {test_java_fail}
            if [ "$?" -eq 0 ]; then
                echo "6) Generate pass and fail test done"
            else
                exit 6
            fi

            # Compile pass and fail test
            javac -cp {bin}:{self.junit_jar}:{self.hamcrest_jar} {test_java_pass} {test_java_fail} -d {bin}
            if [ "$?" -eq 0 ]; then
                echo "7) Compile pass and fail test done"
            else
                exit 7
            fi
            # Run pass test
            java -cp {bin}:{self.clover_jar}:{self.junit_jar}:{self.hamcrest_jar} org.junit.runner.JUnitCore RegressionPassTest0 
            if [ "$?" -eq 0 ]; then
                echo "8) Run pass test done"
            else
                echo exit 8;
            fi

            # Generate clover_html for pass test
            java -cp {self.clover_jar} com.atlassian.clover.reporters.html.HtmlReporter -i {db} -o {pass_result}
            if [ "$?" -eq 0 ]; then
                echo "9) Store result for pass test done"
            else
                exit 9;
            fi

            # Remove clover.db...
            cd {test_dir} && rm -rf clover.db[!.]*
            if [ "$?" -eq 0 ]; then
                echo "10) Remove tmp clover.db done"
            else
                exit 10;
            fi

            # Run fail test
            java -cp {bin}:{self.clover_jar}:{self.junit_jar}:{self.hamcrest_jar} org.junit.runner.JUnitCore RegressionFailTest0
            if [ "$?" -eq 0 ]; then
                echo "11) Run fail test done"
            else 
                echo exit 11;
            fi

            # Generate clover_html for fail test
            java -cp {self.clover_jar} com.atlassian.clover.reporters.html.HtmlReporter -i {db} -o {fail_result}
            if [ "$?" -eq 0 ]; then
                echo "12) Store result for fail test done"
            else 
                exit 12;
            fi

            # Remove clover.db...
            cd {test_dir} && rm -rf clover.db*
            if [ "$?" -eq 0 ]; then
                echo "13) Remove tmp clover.db done"
            else
                exit 13;
            fi
        """
        # debug
        # with open("/home/hieuvd/lvdthieu/check.sh", "w") as f:
        #     f.write(cmd)

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        # debug
        # print(result)
        # print("Command return code:", result.returncode)
        if result.returncode != 0:
            return None, None
        else:
            return pass_result, fail_result

    def execute_row(self, row):
        """
        Executes the test cases for a given row.

        Args:
            row (dict): The row containing the project name and relative path.

        Returns:
            Tuple[str, str]: The pass test info URL and the fail test info URL.
        """
        # print(f"Executing row: {row}")
        try:
            filled_file, orginal_file = self.fill_file(row)
        except Exception:
            # print(f"Error filling file for row: {row}")
            return None, None

        if not filled_file:
            # print(f"Error filling file for row: {row}")
            return None, None
        pass_test_info_url, fail_test_info_url = None, None
        try:
            path_to_file = f"{self.project_storage_dir}/{row['proj_name']}/{row['relative_path']}"
            with open(
                path_to_file, "w", encoding="utf-8", errors="ignore"
            ) as f:
                f.write(filled_file)
            # print(f"Wrote filled file: {path_to_file}")
            pass_test_info_url, fail_test_info_url = self.get_test_info(row)
        except Exception:
            with open(f"/home/hieuvd/lvdthieu/logging{self.index}.txt", 'a', encoding='utf-8') as log:
                log.write(dict(row))
                log.write("-" * 100)
            # print(f"Error executing test for row: {row}")
            return None, None
        finally:
            # print("Wrote original file back to project storage")
            with open(
                path_to_file, "w", encoding="utf-8", errors="ignore"
            ) as f:
                f.write(orginal_file)

        # print(f"Executed row: {row}")
        return pass_test_info_url, fail_test_info_url

    def execute(self):
        """
        Executes the test cases for each row in the DataFrame.
        This function iterates over each row in the DataFrame and executes
        the test cases for that row. It uses the `execute_row` method to
        get the pass and fail test info URLs for each row.
        The pass and fail test info URLs are then appended to the respective lists.
        After executing a certain number of test cases (specified by the `counter` variable),
        the function saves the current state of the DataFrame to a Parquet file.
        This includes the pass and fail test info URLs for all the executed test cases.
        Finally, the pass and fail test info URLs are added as columns to the DataFrame.

        Args:
            None

        Returns:
            None
        """
        pass_test_info_urls, fail_test_info_urls = [], []
        counter = 0
        for _, row in tqdm(
            self.df.iterrows(),
            desc=f"proc {self.index}",
            total=len(self.df),
            position=self.index,
        ):
            counter += 1
            pass_test_info_url, fail_test_info_url = self.execute_row(row)
            pass_test_info_urls.append(pass_test_info_url)
            fail_test_info_urls.append(fail_test_info_url)

            if counter % 50 == 0:
                log_df = self.df.iloc[:counter]
                log_df["pass_test_info_url"] = pass_test_info_urls
                log_df["fail_test_info_url"] = fail_test_info_urls
                log_df.to_parquet(
                    f"{self.log_dir}/executor{self.index}.parquet"
                )

        self.df["pass_test_info_url"] = pass_test_info_urls
        self.df["fail_test_info_url"] = fail_test_info_urls


def group_dataframes(
    df_list: List[pd.DataFrame], num_groups: int
) -> List[pd.DataFrame]:
    """
    Group a list of DataFrames into a specified number of groups with roughly equal total rows.

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


def process_dataframes(executor: TestExecutor) -> list:
    """
    Process the dataframes of the executor.

    Args:
        executor (TestExecutor): The executor to process.

    Returns:
        list: The processed dataframes.
    """
    executor.execute()
    return executor.df


def main(args):
    dataframe = pd.read_parquet(args.input)

    # project_groups = dataframe.groupby(by="proj_name")
    # dataframes = [project_groups.get_group(x) for x in project_groups.groups]
    # num_proc = min(args.proc, len(dataframes))
    # dataframes = group_dataframes(dataframes, num_proc)
    # if not args.start_end:
    #     start, end = 0, len(dataframes)
    # else:
    #     start, end = map(int, args.start_end.split(":"))
    # dataframes = dataframes[start:end]
    # executors = [
    #     TestExecutor(
    #         df=dataframes[index],
    #         column_to_check=args.column_to_check,
    #         project_storage_dir=args.project_storage_dir,
    #         test_dir=args.test_dir,
    #         log_dir=args.log_dir,
    #         index=index,
    #         mvn=args.mvn,
    #         clover_jar=args.clover_jar,
    #         junit_jar=args.junit_jar,
    #         hamcrest_jar=args.hamcrest_jar,
    #         separator_code=args.separator_code,
    #     )
    #     for index in range(len(dataframes))
    # ]

    # with Pool(args.proc) as pool:
    #     results = pool.map(process_dataframes, executors)

    # final_result = pd.concat(results, axis=0)
    # final_result.to_parquet(args.output)
    dataframe = dataframe.iloc[:100]
    executor = TestExecutor(
        df=dataframe,
        column_to_check=args.column_to_check,
        project_storage_dir=args.project_storage_dir,
        test_dir=args.test_dir,
        log_dir=args.log_dir,
        index=0,
        mvn=args.mvn,
        clover_jar=args.clover_jar,
        junit_jar=args.junit_jar,
        hamcrest_jar=args.hamcrest_jar,
        separator_code=args.separator_code,
    )
    result = executor.execute()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input", required=True)
    parser.add_argument("--output", dest="output", required=True)
    parser.add_argument("--col", dest="column_to_check", required=True)
    parser.add_argument("--base-dir", dest="project_storage_dir", required=True)
    parser.add_argument("--test-dir", dest="test_dir", required=True)
    parser.add_argument("--log-dir", dest="log_dir", required=True)
    parser.add_argument("--mvn", dest="mvn", required=True)
    parser.add_argument("--clover-jar", dest="clover_jar", required=True)
    parser.add_argument("--junit-jar", dest="junit_jar", required=True)
    parser.add_argument("--hamcrest-jar", dest="hamcrest_jar", required=True)
    parser.add_argument(
        "--separator-code", dest="separator_code", required=True
    )
    parser.add_argument("--proc", dest="proc", type=int, required=True)
    parser.add_argument("--start-end", dest="start_end")

    args = parser.parse_args()

    main(args)
