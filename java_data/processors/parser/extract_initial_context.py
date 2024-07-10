import argparse
import json
import logging
import os
from subprocess import run

import pandas as pd
from tqdm import tqdm


def get_context(json_dir, project_name, qualified_name):
    with open(f"{json_dir}/{project_name}_type.json", "r") as f:
        types = json.load(f)
    for type in types:
        if type["qualified_name"] == qualified_name:
            return type["abstract"]
    return "<not_self_defined_class>"


def processor(args):
    df, parser, base_dir, json_dir, class_path, index, log_dir = args
    logger = logging.Logger(f"extract_initial_context", logging.INFO)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    else:
        os.system(f"rm -rf {log_dir}/*")
    logger.addHandler(
        logging.FileHandler(f"{log_dir}/extract_initial_context_{index}.log")
    )
    initial_context = []
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
            f"{row['func_name']}"
        )
        try:
            result = run(cmd, shell=True, text=True, capture_output=True)
            output = result.stdout.strip()
            print(output)
            # match output:
            #     case (
            #         "<encounter_error>"
            #         | "<no_class>"
            #         | "<cant_find_class>"
            #         | "<cant_resolve_binding>"
            #         | "<super_class_null>"
            #     ):
            #         logger.error(
            #             "{:<25} {:<40} {}".format(
            #                 output, row["proj_name"], row["relative_path"]
            #             )
            #         )
            #         initial_context.append("<no_super_class>")
            #     case "<no_super_class>":
            #         logger.info(
            #             "{:<40} {} {}".format(
            #                 row["proj_name"],
            #                 row["relative_path"],
            #                 "has no super class",
            #             )
            #         )
            #         initial_context.append("<no_super_class>")
            #     case _:
            #         logger.info(
            #             "{:<40} {} {}".format(
            #                 row["proj_name"],
            #                 row["relative_path"],
            #                 "has super class",
            #             )
            #         )
            #         super_class_context = get_context(
            #             json_dir,
            #             row["proj_name"],
            #             qualified_name=output,
            #         )
            #         initial_context.append(super_class_context)
            if output == "<encounter_error>":
                logger.error(
                    "{:<25} {:<40} {}".format(
                        output, row["proj_name"], row["relative_path"]
                    )
                )
                initial_context.append("<no_param_class")
            elif not output:
                logger.info(
                    "{:<40} {} {}".format(
                        row["proj_name"],
                        row["relative_path"],
                        "has no param class",
                    )
                )
                initial_context.append("<no_param_class>")
            else:
                param_types = output.split("\n")
                param_type_contexts = ""
                for param_type in param_types:
                    param_type_context = get_context(
                        json_dir,
                        row["proj_name"],
                        qualified_name=param_type,
                    )
                    if param_type_context != "<not_self_defined_class>":
                        param_type_contexts += (
                            param_type_context + "<param_class>"
                        )
                if param_type_contexts:
                    initial_context.append(param_type_contexts)
                    logger.info(
                        "{:<40} {} {}".format(
                            row["proj_name"],
                            row["relative_path"],
                            "has param class",
                        )
                    )
                else:
                    initial_context.append("<not_self_defined_class>")
                    logger.info(
                        "{:<40} {} {}".format(
                            row["proj_name"],
                            row["relative_path"],
                            "has not self defined class",
                        )
                    )
        except:
            logger.error(
                "{:<25} {:<40} {}".format(
                    "<run_command>", row["proj_name"], row["relative_path"]
                )
            )
            initial_context.append("<error>")
        cnt += 1
        if cnt % 100 == 0:
            log_df = df.iloc[:cnt]
            log_df["initial_context"] = initial_context
            log_df.to_parquet(f"{log_dir}/log_extract_initial_context.parquet")
    df["param_context"] = initial_context
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
    args = parser.parse_args()
    main(args)
