import argparse
import codecs
import re
from typing import Optional

import pandas as pd
from make_data.run import get_functions, get_location
from tqdm import tqdm


def clear_compiler_feedback(
    row: pd.Series,
    project_dir: str = "/home/hieuvd/lvdthieu/repos/tmp-projects",
    column: str = "generated_code",
) -> Optional[str]:
    """Clear compiler feedback
    Args:
        row (pd.core.series.Series): Row
        project_dir (str, optional): Project directory. Defaults to "/home/hieuvd/lvdthieu/repos/tmp-projects".
        column (str, optional): Column to clear. Defaults to "generated_code".

    Returns:
        Optional[str]: New compiler feedback
    """
    if row.compiler_feedback == "<success>":
        return "<success>"
    elif row.compiler_feedback == "<execute_error>":
        return "<execute_error>"

    file_path = f"{project_dir}/{row.proj_name}/{row.relative_path}"
    with codecs.open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        file_contents = file.read().replace("\r\n", "\n")

    filled_class = row.masked_class.replace("<FILL_FUNCTION_BODY>", row[column])

    functions = get_functions(file_contents)
    if not functions:
        return None

    for function in functions:
        if (
            function["class_name"] == row.class_name
            and function["func_name"] == row.func_name
        ):
            class_start, class_end = get_location(
                file_contents, function["class_loc"]
            )
            filled_file = (
                file_contents[:class_start]
                + filled_class
                + file_contents[class_end:]
            )
            errors = row.compiler_feedback.split("\n")
            new_errors = []
            for error in errors:
                try:
                    error_components = re.search(
                        r"<file>(.*?)<line>(\d+)<col>(\d+)<err>(.*)",
                        error,
                    ).groups()
                    if (
                        error_components[0]
                        == f"{project_dir}/{row.proj_name}/{row.relative_path}"
                    ):
                        code_lines = filled_file.splitlines() + [""]
                        error_line = code_lines[int(error_components[1]) - 1]
                        error_msg = (
                            f"<file>{error_components[0].replace(project_dir + '/', '')}"
                            f"<line>{error_components[1]}"
                            f"<col>{error_components[2]}"
                            f"<line_of_code>{error_line}"
                            f"<err>{error_components[3]}"
                        )
                        new_errors.append(error_msg)
                    else:
                        new_errors.append(error)
                except Exception:
                    pass

            return "\n".join(new_errors)
    return None


def main(input_path, output_path, column):
    df = pd.read_parquet(input_path)
    new_feedbacks = [
        clear_compiler_feedback(row, column=column)
        for _, row in tqdm(
            df.iterrows(), total=len(df), desc="Clearing compiler feedback"
        )
    ]

    df["new_compiler_feedback"] = new_feedbacks
    df.to_parquet(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up compiler feedback")
    parser.add_argument("--input", type=str, help="Input file path")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument(
        "--column",
        type=str,
        default="generated_code",
        help="Name of the column to clear",
    )

    args = parser.parse_args()
    main(args.input, args.output, args.column)
