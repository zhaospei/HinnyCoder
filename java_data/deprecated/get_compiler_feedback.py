import argparse
import codecs
import logging
import re
from functools import wraps
from subprocess import run
from time import time
from typing import Dict, List, NamedTuple, Optional, Tuple

import pandas as pd
from antlr4 import *
from java8.JavaLexer import JavaLexer
from java8.JavaParser import JavaParser
from java8.JavaParserListener import JavaParserListener
from tqdm import tqdm


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


class CompilerFeedback(NamedTuple):
    project_name: str
    feedback: str


class FileInfo(NamedTuple):
    project_name: str
    relative_path: str


class ErrorInfo(NamedTuple):
    error_info: str


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print(
            "func:%r args:[%r, %r] took: %2.4f sec"
            % (f.__name__, args, kw, te - ts)
        )
        return result

    return wrap


class CompilableChecker:
    def __init__(
        self,
        df: pd.DataFrame,
        column_to_check: str,
        proj_storage_dir: str,
        tmp_dir: str,
        mvn: str,
        logger: logging.Logger,
    ):
        """Constructor
        Args:
            df (pd.DataFrame): Dataframe of java code
            column_to_check (str): Column to check
            proj_storage_dir (str): Project storage directory
            tmp_dir (str): Temporary directory (to store a copy of project)
            output (str): Output
        """
        self.df = df
        self.column_to_check = column_to_check
        self.proj_storage_dir = proj_storage_dir
        self.tmp_dir = tmp_dir
        self.projects = set(df["proj_name"].to_list())
        self.mvn = mvn
        self.logger = logger

    def copy_project_to_tmp_dir(self):
        """Copy project to temporary directory"""
        for project in tqdm(self.projects, desc="Copying projects"):
            path_to_project = "{}/{}".format(self.proj_storage_dir, project)
            # if not os.path.exists("{}/{}".format(self.tmp_dir, project)):
            run(f"cp -Rf {path_to_project} {self.tmp_dir}", shell=True)

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
                    return filled_file
            return None
        else:
            return None

    def modified_files(self):
        """Replace original file with file with generated code"""
        for _, row in tqdm(
            self.df.iterrows(), desc="Modifying files", total=len(self.df)
        ):
            path_to_file = "{}/{}/{}".format(
                self.tmp_dir, row["proj_name"], row["relative_path"]
            )
            filled_file = self._fill_file(row)
            # If fail log file path into error file
            try:
                if not filled_file:
                    raise LookupError(
                        "There is an error while filling file {}".format(
                            path_to_file
                        )
                    )
                else:
                    with open(path_to_file, "w") as f:
                        f.write(filled_file)
            except LookupError as e:
                self.logger.error(e)
            except:
                self.logger.error(
                    "Error while modifying file {}".format(path_to_file)
                )

    def extract_error(
        self, compile_info: List[CompilerFeedback]
    ) -> Dict[FileInfo, ErrorInfo]:
        """Extract error from feedback
        Args:
            compile_info (List[CompilerFeedback]): Compiler feedback
        Returns:
            Dict[FileInfo, ErrorInfo]: Error info
        """
        error_files: Dict[FileInfo, ErrorInfo] = {}
        err_pattern = r"^\[ERROR\] (?P<file>.+?):\[(?P<line>\d+),(?P<col>\d+)\] (?P<err>.+)$"
        for project_name, feedback in compile_info:
            errors = set(re.findall(err_pattern, feedback, re.MULTILINE))
            for error in errors:
                try:
                    file, line, col, err = error
                    relative_path = file.split(project_name)[1][1:]
                    file_error = (
                        f"""Line: {line}, Column: {col}, Error: {err})\n"""
                    )
                    error_files[
                        FileInfo(
                            project_name=project_name,
                            relative_path=relative_path,
                        )
                    ] = ErrorInfo(error_info=file_error)
                except:
                    logger.info("Can not parse error", file, line, col, err)
        return error_files

    @timing
    def add_compile_info(self) -> pd.DataFrame:
        """Add compile info to dataframe
        Returns:
            pd.DataFrame: Dataframe with compile info
        """
        compile_info: List[CompilerFeedback] = []
        for project in tqdm(self.projects, desc="Compiling project"):
            path_to_project = "{}/{}".format(self.tmp_dir, project)
            cmd = f"""
            cd {path_to_project}
            cd $(ls -d */|head -n 1)
            {self.mvn} clean compile
            """
            data = run(cmd, shell=True, capture_output=True, text=True)
            compile_info.append(CompilerFeedback(project, data.stdout))

        error_files = self.extract_error(compile_info)

        def get_compile_info(row):
            error = error_files.get(
                FileInfo(
                    project_name=row["proj_name"],
                    relative_path=row["relative_path"],
                ),
                None,
            )
            return error.error_info if error else "<COMPILED_SUCCESSFULLY>"

        df["compile_info"] = df.apply(get_compile_info, axis=1)
        return df

    def get_compilable_feedback(self):
        """Get compilable feedback"""
        self.copy_project_to_tmp_dir()
        print("Copy projects to temp directory done")
        self.modified_files()
        print("Modify files done")
        new_df = self.add_compile_info()
        return new_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--input-type", dest="type")
    parser.add_argument("--output", dest="output")
    parser.add_argument("--dir", dest="dir")
    parser.add_argument("--tmp", dest="tmp")
    parser.add_argument("--col", dest="col")
    parser.add_argument("--mvn", dest="mvn")
    parser.add_argument("--logfile", dest="logfile")
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.logfile,
        filemode="a",
        format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("get_compilable_feedback")

    match args.type:
        case "jsonl":
            df = pd.read_json(args.input, lines=True)
        case "parquet":
            df = pd.read_parquet(args.input, "fastparquet")
        case "csv":
            df = pd.read_csv(args.input)
    print("Read input done")
    compiler_checker = CompilableChecker(
        df=df,
        column_to_check=args.col,
        proj_storage_dir=args.dir,
        tmp_dir=args.tmp,
        mvn=args.mvn,
        logger=logger,
    )
    result = compiler_checker.get_compilable_feedback()
    print(
        "Compilable rate: {:.2%}".format(
            len(result[result["compile_info"] == "<COMPILED_SUCCESSFULLY>"])
            / len(result)
        )
    )
    result.to_parquet(args.output, "fastparquet")
