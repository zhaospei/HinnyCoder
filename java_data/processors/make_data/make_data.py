import argparse
import codecs
import multiprocessing as mp
import random
import re
from typing import List, NamedTuple, Optional, Tuple

import pandas as pd
from antlr4 import *
from make_data.java.java8.JavaLexer import JavaLexer
from make_data.java.java8.JavaParser import JavaParser
from make_data.java.java8.JavaParserListener import JavaParserListener
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--input", dest="input")
parser.add_argument("--dir", dest="dir")
parser.add_argument("--output", dest="output")
parser.add_argument("--workers", dest="workers")


class ASample(NamedTuple):
    class_name: str
    func_name: str
    masked_class: str
    func_body: str


class Location(NamedTuple):
    start_line: int
    start_col: int
    end_line: int
    end_col: int


class Function(NamedTuple):
    class_name: str
    class_loc: Location
    func_name: str
    func_body_loc: Location


class ExtractFunc(JavaParserListener):
    def __init__(self):
        super().__init__()
        self.functions = []

    def enterClassDeclaration(self, ctx):
        self.class_name = ctx.identifier().getText()
        self.class_loc = Location(
            ctx.start.line,
            ctx.start.column,
            ctx.stop.line,
            ctx.stop.column + len(ctx.stop.text),
        )

    def enterMethodDeclaration(self, ctx):
        # If method is void method ignore it
        # if ctx.typeTypeOrVoid().getText() == "void":
        #     return
        self.func_name = ctx.identifier().getText()
        body = ctx.methodBody().block()
        if not body:
            return
        self.func_body_loc = Location(
            body.start.line,
            body.start.column,
            body.stop.line,
            body.stop.column + len(body.stop.text),
        )
        try:
            self.functions.append(
                {
                    "class_name": self.class_name,
                    "class_loc": self.class_loc,
                    "func_name": self.func_name,
                    "func_body_loc": self.func_body_loc,
                }
            )
        except:
            pass

    def get_functions(self):
        return self.functions


def get_location(java_code: str, loc: Location) -> Tuple[int, int]:
    lines = java_code.split("\n")
    start_idx = 0
    for i in range(loc.start_line - 1):
        start_idx += len(lines[i])
    start_idx = start_idx + loc.start_col + loc.start_line - 1

    end_idx = 0
    for i in range(loc.end_line - 1):
        end_idx += len(lines[i])
    end_idx = end_idx + loc.end_col + loc.end_line - 1
    return start_idx, end_idx


def count_java_tokens_antlr4(code):
    lexer = JavaLexer(InputStream(code))
    return len(lexer.getAllTokens())


def get_functions(java_code: str) -> Optional[List[Function]]:
    try:
        input_stream = InputStream(java_code)
        lexer = JavaLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = JavaParser(token_stream)
        tree = parser.compilationUnit()
        # Create listener
        listener = ExtractFunc()
        # Walk the parse tree
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        functions = listener.get_functions()
    except:
        return None
    return functions


def mask_function(java_code: str) -> Optional[ASample]:
    functions = get_functions(java_code)
    if not functions:
        return None
    # Randomly select a function
    random_function = random.choice(functions)

    # Extract function body
    class_start_idx, class_end_idx = get_location(
        java_code, random_function.class_loc
    )
    func_body_start_idx, func_body_end_idx = get_location(
        java_code, random_function.func_body_loc
    )
    masked_class = (
        java_code[class_start_idx : func_body_start_idx + 1]
        + "<FILL_FUNCTION_BODY>"
        + java_code[func_body_end_idx - 1 : class_end_idx]
    )
    func_body = java_code[func_body_start_idx + 1 : func_body_end_idx - 1]

    return ASample(
        class_name=random_function.class_name,
        func_name=random_function.func_name,
        masked_class=masked_class,
        func_body=func_body,
    )


def modified_mask_function(java_code: str) -> Optional[List[ASample]]:
    functions = get_functions(java_code)
    if not functions:
        return None

    # Weighted random a function based on function body length
    # the more function long, the more probability it would be chose
    def get_len(java_code: str, loc: Location) -> int:
        start_idx, end_idx = get_location(java_code, loc)
        return count_java_tokens_antlr4(java_code[start_idx:end_idx])

    # functions_with_len_body = [
    #     [get_len(java_code, func.func_body_loc), func] for func in functions
    # ]
    # functions_with_len_body.sort(key=lambda x: x[0])
    # weights, functions = zip(*functions_with_len_body)
    # weights = list(weights)
    # functions = list(functions)
    # for i in range(1, len(weights)):
    #     weights[i] = weights[i - 1] + weights[i]
    # raw_weights = [
    #     get_len(java_code, func["func_body_loc"]) for func in functions
    # ]
    # total = sum(raw_weights)
    # weights = [weight / total for weight in raw_weights]
    # random_function = random.choices(functions, weights=weights, k=1)[0]
    result = []
    for function in functions:
        # Extract function body
        class_start_idx, class_end_idx = get_location(
            java_code, function["class_loc"]
        )
        func_body_start_idx, func_body_end_idx = get_location(
            java_code, function["func_body_loc"]
        )
        masked_class = (
            java_code[class_start_idx : func_body_start_idx + 1]
            + "<FILL_FUNCTION_BODY>"
            + java_code[func_body_end_idx - 1 : class_end_idx]
        )
        func_body = java_code[func_body_start_idx + 1 : func_body_end_idx - 1]

        result.append(
            ASample(
                class_name=function["class_name"],
                func_name=function["func_name"],
                masked_class=masked_class,
                func_body=func_body,
            )
        )
    return result


def make_samples(argument: Tuple[str, str, str]):
    java_file_url, project_name, relative_path = argument
    with codecs.open(
        java_file_url, "r", encoding="utf-8", errors="ignore"
    ) as f:
        try:
            java_code = f.read()
            # sample = mask_function(java_code)
            samples = modified_mask_function(java_code)
            if samples:
                return [
                    {
                        "proj_name": project_name,
                        "relative_path": relative_path,
                        "class_name": sample.class_name,
                        "func_name": sample.func_name,
                        "masked_class": sample.masked_class,
                        "func_body": sample.func_body,
                    }
                    for sample in samples
                ]
            else:
                return [
                    {
                        "proj_name": project_name,
                        "relative_path": relative_path,
                        "class_name": None,
                        "func_name": None,
                        "masked_class": None,
                        "func_body": None,
                    }
                ]
        except:
            return [
                {
                    "proj_name": None,
                    "relative_path": None,
                    "class_name": None,
                    "func_name": None,
                    "masked_class": None,
                    "func_body": None,
                }
            ]


def make_dataset(
    java_files: pd.DataFrame, repos_directory: str, num_process: int = 10
) -> pd.DataFrame:
    """Make dataset

    Args:
        java_file_urls (str): java file urls
        repos_directory (str): path to diretory of repositories
        num_process (int): number of concurrent processes. Default: 10.

    Returns:
        pd.DataFrame: Dataset
    """
    iteration = len(java_files)
    tqdm.pandas(desc="Making absolute url")
    java_files["absolute_url"] = java_files["java_file_urls"].progress_apply(
        lambda file: f"{repos_directory}/{file}"
    )

    arguments = list(
        zip(
            java_files["absolute_url"],
            java_files["proj_name"],
            java_files["relative_path"],
        )
    )
    # rows = []
    # for args in arguments:
    #     tmp = make_samples(args)
    #     print(tmp)
    #     # rows.append(tmp)
    #     # rows.append(make_samples(args))
    #     break
    with mp.Pool(processes=num_process) as pool:
        rows = list(
            tqdm(
                pool.imap(make_samples, arguments),
                total=iteration,
                desc="Making data",
            )
        )
    flatten_rows = []
    for item in rows:
        flatten_rows.extend(item)
    return pd.DataFrame(flatten_rows)


def post_processing(dataset: pd.DataFrame) -> pd.DataFrame:
    std = lambda x: re.sub(r"[\t\n\r ]", "", x)
    dataset["std_func_body"] = dataset["func_body"].apply(std)
    dataset = dataset[dataset["std_func_body"] != ""]
    dataset.drop(columns=["std_func_body"], inplace=True)
    dataset.reset_index(drop=True, inplace=True)
    return dataset


def main(args):
    java_files = pd.read_parquet(args.input)
    java_files.reset_index(drop=True, inplace=True)
    df = make_dataset(
        java_files=java_files,
        repos_directory=args.dir,
        num_process=int(args.workers),
    )
    df.to_parquet(args.output, "fastparquet")


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
