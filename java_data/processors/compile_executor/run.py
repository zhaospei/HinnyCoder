import argparse
import logging
import multiprocessing
import os
import re
import subprocess
import sys
import warnings
from typing import List, Optional

import pandas as pd

warnings.filterwarnings("ignore")

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/..")
from make_data.run import get_functions, get_location
from tqdm import tqdm


class CompilerExecutor:
    def __init__(
        self,
        df: pd.DataFrame = pd.DataFrame(),
        column_to_check: str = "generated_code",
        proj_storage_dir: str = "",
        log_dir: str = "./log_compile",
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
        print(functions)
        print(row["class_name"], row["func_name"])
        print("-" * 100)
        if functions:
            print("Functions")
            for function in functions:
                print(function["class_name"], function["func_name"])
                if (
                    function["class_name"] == row["class_name"]
                    and function["func_name"] == row["func_name"]
                ):
                    print("Here")
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
            f"&& {self.mvn} clean compile -DskipTests -Dcheckstyle.skip -Dgpg.skip -Dlicense.skip"
        )
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.stdout, res.returncode

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
                    self.logger.info("\tPrepare to replace origin file")
                    with open(
                        path_to_file, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        f.write(filled_file)
                    self.logger.info("\tAlready replaced origin file")
                    compile_info, returncode = self._get_compiler_feedback(row)
                    self.logger.info("\tGot compile info successfully")
                    # Debug
                    # print(compile_info, returncode)
                    compiler_feedback = self._extract_error(compile_info)
                    self.logger.info("\tExtracted error successfully")
                except Exception:
                    self.logger.error("\tEncounter error while executing")
                    raise Exception("Encounter exception when executing")
                finally:
                    with open(
                        path_to_file, "w", encoding="utf-8", errors="ignore"
                    ) as f:
                        f.write(original_file)
                    self.logger.info("\tWrote back")
            compilable = "<success>" if not returncode else "<fail>"
        except Exception:
            compiler_feedback = "<execute_error>"
            compilable = "<execute_error>"
            print(row["relative_path"])
        return compiler_feedback, compilable

    def execute(self):
        lst_compiler_feedback = []
        lst_compilable = []
        counter = 0
        for _, row in tqdm(
            self.df.iterrows(),
            desc=f"Proc {self.index}",
            total=len(self.df),
            position=self.index,
        ):
            counter += 1
            compiler_feedback, compilable = self._execute(row)
            lst_compiler_feedback.append(compiler_feedback)
            lst_compilable.append(compilable)
            if counter % 10 == 0:
                log_df = self.df.iloc[:counter]
                log_df["compiler_feedback"] = lst_compiler_feedback
                log_df["compilable"] = lst_compilable
                log_df.to_parquet(
                    f"{self.log_dir}/executor{self.index}.parquet"
                )
        return lst_compiler_feedback, lst_compilable


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
    lst_compiler_feedback, lst_compilable = compiler.execute()
    df["compiler_feedback"] = lst_compiler_feedback
    df["compilable"] = lst_compilable
    return df


# retry = [
#     "spring-cloud-gateway/spring-cloud-gateway-server-mvc/src/main/java/org/springframework/cloud/gateway/server/mvc/filter/Bucket4jFilterFunctions.java",
#     "frontend-maven-plugin/frontend-plugin-core/src/main/java/com/github/eirslett/maven/plugins/frontend/lib/ProxyConfig.java",
#     "logstash-logback-encoder/src/main/java/net/logstash/logback/appender/AsyncDisruptorAppender.java",
#     "logstash-logback-encoder/src/main/java/net/logstash/logback/appender/listener/FailureSummaryAppenderListener.java",
#     "logstash-logback-encoder/src/main/java/net/logstash/logback/composite/AbstractCompositeJsonFormatter.java",
#     "jitsi/modules/impl/protocol-sip/src/main/java/net/java/sip/communicator/impl/protocol/sip/xcap/model/xcaperror/UniquenessFailureType.java",
#     "AutoLoadCache/autoload-cache-manager/autoload-cache-manager-jedis/src/main/java/com/jarvis/cache/redis/ShardedJedisCacheManager.java",
#     "orientdb/server/src/main/java/com/orientechnologies/orient/server/distributed/operation/NodeOperationTask.java",
#     "jitsi/modules/plugin/desktoputil/src/main/java/net/java/sip/communicator/plugin/desktoputil/plaf/SIPCommTabbedPaneEnhancedUI.java",
#     "graphhopper/reader-gtfs/src/main/java/com/conveyal/gtfs/model/Calendar.java",
#     "kafdrop/src/main/java/kafdrop/config/HealthCheckConfiguration.java",
#     "kafdrop/src/main/java/kafdrop/config/InterceptorConfiguration.java",
#     "kafdrop/src/main/java/kafdrop/config/MessageFormatConfiguration.java",
#     "snowflake/muon-jediterm/src/main/java/com/jediterm/terminal/HyperlinkStyle.java",
#     "mapstruct/processor/src/main/java/org/mapstruct/ap/internal/model/MapMappingMethod.java",
#     "kafdrop/src/main/java/kafdrop/model/TopicPartitionVO.java",
#     "mini-spring/src/main/java/org/springframework/aop/framework/CglibAopProxy.java",
#     "mini-spring/src/main/java/org/springframework/core/convert/support/StringToNumberConverterFactory.java",
#     "pmd/pmd-java/src/main/java/net/sourceforge/pmd/lang/java/symbols/table/coreimpl/MostlySingularMultimap.java",
#     "jitsi/modules/util/src/main/java/net/java/sip/communicator/util/Html2Text.java",
#     "unirest-java/unirest-modules-mocks/src/main/java/kong/unirest/core/Times.java",
#     "truth/core/src/main/java/com/google/common/truth/Correspondence.java",
#     "truth/core/src/main/java/com/google/common/truth/Expect.java",
#     "truth/core/src/main/java/com/google/common/truth/IterableSubject.java",
#     "truth/extensions/proto/src/main/java/com/google/common/truth/extensions/proto/DiffResult.java",
#     "truth/extensions/proto/src/main/java/com/google/common/truth/extensions/proto/IterableOfProtosSubject.java",
#     "javamelody/javamelody-core/src/main/java/net/bull/javamelody/JpaPersistence.java",
#     "javamelody/javamelody-core/src/main/java/net/bull/javamelody/JspWrapper.java",
#     "javamelody/javamelody-core/src/main/java/net/bull/javamelody/internal/model/CounterStorage.java",
#     "javamelody/javamelody-core/src/main/java/net/bull/javamelody/internal/model/SamplingProfiler.java",
# ]


def main(args):
    df = pd.read_json(args.input, lines=True)
    # df = df[df["relative_path"].isin(retry)][:1]
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
    print(
        "\n\n\n\n\nCompilation rate: {:.2f}".format(
            100
            * len(final_result[final_result["compilable"] == "<success>"])
            / len(final_result)
        )
    )
    final_result.to_json(args.output, lines=True, orient="records")


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
