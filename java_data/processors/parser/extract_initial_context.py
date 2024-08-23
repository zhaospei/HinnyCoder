import argparse
import json
import logging
import os
import subprocess

import pandas as pd
from tqdm import tqdm


def get_context(json_dir: str, project_name: str, qualified_name: str) -> str:
    """Get abstract implementation of java class corresponding to
        `project_name` and `qualified_name`

    Args:
        json_dir (str): Where store parsed project result json files
        project_name (str): Project name
        qualified_name (str): Class qualified name

    Returns:
        str: Abstract implementation of java class if qualified name is in
        parsed project json file else return <not_self_defined_class>
    """
    with open(f"{json_dir}/{project_name}_type.json", "r") as f:
        types = json.load(f)
    for type in types:
        if type["qualified_name"] == qualified_name:
            return type["abstract"]
    return "<not_self_defined_class>"


def processor(args):
    df, parser, base_dir, json_dir, class_path, index, log_dir, task = args
    logger = logging.Logger("extract_initial_context", logging.INFO)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    else:
        os.system(f"rm -rf {log_dir}/*")
    logger.addHandler(
        logging.FileHandler(f"{log_dir}/extract_initial_context_{index}.log")
    )
    context = []
    cnt = 0
    for _, row in tqdm(
        df.iterrows(), total=len(df), desc=f"Proc {index}", position=index
    ):
        cmd = (
            f"cd {parser}/target/classes "
            f"&& java -cp {class_path} "
            "Main "
            f"{base_dir} "
            f"{row['proj_name']} "
            f"{row['relative_path']} "
            f"{row['class_name']} "
            f"{row['func_name']} "
            f"{task}"
        )
        try:
            result = subprocess.run(
                cmd, shell=True, text=True, capture_output=True
            )
            output = result.stdout.strip()
            if output == "<encounter_error>":
                logger.error(
                    "{:<25} {:<40} {}".format(
                        output, row["proj_name"], row["relative_path"]
                    )
                )
                if task == "param":
                    context.append("<no_param_class")
                else:
                    context.append("<no_parent_class>")
            elif not output:
                logger.info(
                    "{:<40} {:<160} has no {} class".format(
                        row["proj_name"],
                        row["relative_path"],
                        task,
                    )
                )
                if task == "param":
                    context.append("<no_param_class")
                else:
                    context.append("<no_parent_class>")
            else:
                types = output.split("\n")
                type_context = ""
                for type in types:
                    ctx = get_context(
                        json_dir,
                        row["proj_name"],
                        qualified_name=type,
                    )
                    if ctx != "<not_self_defined_class>":
                        type_context += ctx + "\n"
                if type_context:
                    context.append(type_context)
                    logger.info(
                        "{:<40} {:<160} has {} class".format(
                            row["proj_name"],
                            row["relative_path"],
                            task,
                        )
                    )
                else:
                    context.append("<not_self_defined_class>")
                    logger.info(
                        "{:<40} {:<160} has not self defined class".format(
                            row["proj_name"], row["relative_path"]
                        )
                    )
        except Exception:
            logger.error(
                "{:<25} {:<40} {}".format(
                    "<run_command_error>",
                    row["proj_name"],
                    row["relative_path"],
                )
            )
            context.append("<error>")
        cnt += 1
        if cnt % 100 == 0:
            log_df = df.iloc[:cnt]
            log_df["context"] = context
            log_df.to_parquet(f"{log_dir}/log_extract_initial_context.parquet")
    df[f"{task}_context"] = context
    return df


def main(args):
    df = pd.read_parquet(args.input)
    class_path = "." f":'{args.parser}/target/dependency/*'"
    new_df = processor(
        (
            df,
            args.parser,
            args.base_dir,
            args.json_dir,
            class_path,
            0,
            args.log_dir,
            args.task,
        )
    )
    new_df.to_parquet(args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--parser", dest="parser")
    parser.add_argument("--base-dir", dest="base_dir")
    parser.add_argument("--json-dir", dest="json_dir")
    parser.add_argument("--num-proc", dest="num_proc")
    parser.add_argument("--log-dir", dest="log_dir")
    parser.add_argument("--task", dest="task", choices=["parent", "param"])
    args = parser.parse_args()
    main(args)
