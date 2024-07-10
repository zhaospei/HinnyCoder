import argparse
import json
from collections import defaultdict
from typing import Dict, List, Optional

import pandas as pd
from antlr4 import *
from java.java8.JavaLexer import JavaLexer
from java.java8.JavaParser import JavaParser
from java.java8.JavaParserListener import JavaParserListener
from make_data import Location, get_location
from tqdm import tqdm


class ExtractSignatureAndVar(JavaParserListener):
    """Extract signature and variables in a class"""

    def __init__(self, java_code: str):
        """Constructor

        Args:
            java_code (str): Java code
        """
        super().__init__()
        self.class_comp = defaultdict(list)
        self.java_code = java_code

    def enterClassDeclaration(self, ctx):
        self.class_name = ctx.identifier().getText()

    def enterMethodDeclaration(self, ctx):
        self.func_name = ctx.identifier().getText()
        body = ctx.methodBody().block()
        func_start_idx, func_end_idx = get_location(
            self.java_code,
            Location(
                ctx.start.line,
                ctx.start.column,   
                ctx.stop.line,
                ctx.stop.column + len(ctx.stop.text),
            ),
        )
        if body:
            func_body_start_idx, _ = get_location(
                self.java_code,
                Location(
                    body.start.line,
                    body.start.column,
                    body.stop.line,
                    body.stop.column + len(body.stop.text),
                ),
            )
            self.class_comp[self.class_name].append(
                self.java_code[func_start_idx:func_body_start_idx] + "{}"
            )
        else:
            self.class_comp[self.class_name].append(
                self.java_code[func_start_idx:func_end_idx]
            )

    def enterFieldDeclaration(self, ctx):
        variable_name = ctx.variableDeclarators().getText()
        variable_type = ctx.typeType().getText()
        self.class_comp[self.class_name].append(
            "%s %s;" % (variable_type, variable_name)
        )

    def get_class_comp(self):
        return self.class_comp


def extract_signature_and_var(java_code: str) -> Optional[str]:
    """Extract signature and variables in a class

    Args:
        java_code (str): Java code

    Returns:
        Optional[str]: Signature and variables
    """
    if not java_code:
        return None
    try:
        input_stream = InputStream(java_code)
        lexer = JavaLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = JavaParser(token_stream)
        tree = parser.compilationUnit()
        # Create listener
        listener = ExtractSignatureAndVar(java_code)
        # Walk the parse tree
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        class_comps = listener.get_class_comp()
        return ','.join(class_comps)
    except:
        return None


def get_code(classQualifiedName: str, class_info: Dict) -> str:
    """Return class code

    Args:
        classQualifiedName (str): Class qualified name
        class_info (Dict): Class info

    Returns:
        Optional[str]: Class code
    """
    if not classQualifiedName:
        return None
    for cls in class_info:
        if cls["classInfos"]["classQualifiedName"] == classQualifiedName:
            return cls["classInfos"]["sourceCode"]
    return None


def get_parent_class_code(row: pd.Series, storage_url: str) -> Optional[str]:
    """Return parent class code

    Args:
        row (pd.Series):
        storage_url (str): Parsed project storage

    Returns:
        Optional[str]: If class in row have parent class return it or None in contrast
    """
    parsed_project_path = "{}/parsed_{}.json".format(storage_url, row["proj_name"])
    with open(parsed_project_path, "r") as f:
        class_info = json.load(f)
    for cls in class_info:
        cls_relative_path = cls["classInfos"]["filePath"].replace(
            cls["projectPath"] + "/", ""
        )
        if (
            cls_relative_path == row["relative_path"]
            and cls["classInfos"]["className"] == row["class_name"]
        ):
            if cls["classInfos"]["extendedClassQualifiedName"] not in [
                "",
                "java.lang.Object",
            ]:
                parent_class = cls["classInfos"]["extendedClassQualifiedName"]
            else:
                parent_class = None
            break
    else:
        parent_class = None

    parent_class_code = get_code(parent_class, class_info)
    return parent_class_code


def get_extended_classes(class_qualified_name: str, class_info: Dict) -> Optional[List[str]]:
    """Return extended classes

    Args:
        qualified_class_name (str): Qualified class name

    Returns:
        Optional[List[str]]: Extended classes
    """
    extended_classes = []
    while class_qualified_name:
        for cls in class_info:
            if cls["classInfos"]["classQualifiedName"] == class_qualified_name:
                if (cls["classInfos"]["extendedClassQualifiedName"]not in ["","java.lang.Object"]):
                    class_qualified_name = cls["classInfos"]["extendedClassQualifiedName"]
                    extended_classes.append(class_qualified_name)
                else:
                    class_qualified_name = None
                break
        else:
            break
    return extended_classes


def modified_get_parent_class_code(row: pd.Series, storage_url: str) -> Optional[str]:
    """Get parent and ancestor class code
    
    Args:
        row (pd.Series): Row
        storage_url (str): Storage url

    Returns:
        Optional[str]: Parent class code
    """
    parsed_project_path = "{}/parsed_{}.json".format(storage_url, row["proj_name"])
    with open(parsed_project_path, "r") as f:
        class_info = json.load(f)
    
    for cls in class_info:
        if (
            cls["classInfos"]["filePath"].replace(cls["projectPath"] + "/", "")
            == row["relative_path"]
            and cls["classInfos"]["className"] == row["class_name"]
        ):
            class_qualified_name = cls["classInfos"]["classQualifiedName"]
            break
    else:
        class_qualified_name = None
    extended_classes = get_extended_classes(class_qualified_name, class_info)
    if not extended_classes:
        return None, None
    else:
        code = '\n'.join(list(map(lambda x: get_code(x, class_info) if get_code(x, class_info) else "", extended_classes))) 
        if not code or code == "":
            return '\n'.join(extended_classes), None
        else:
            return '\n'.join(extended_classes), code


def add_parent_class_code(df: pd.DataFrame, storage_url: str) -> pd.DataFrame:
    """Get parent class code
    Args:
        df (pd.DataFrame): Dataset
        storage_url (str): Storage url

    Returns:
        pd.DataFrame: Dataset with parent class code (if exist)
    """
    tqdm.pandas(desc="Adding parent class code")
    df[["extended_classes", "parent_class_code"]] = df.progress_apply(
        lambda row: modified_get_parent_class_code(row, storage_url), axis="columns", result_type="expand"
    )
    return df


def get_parent_signature_and_var(df: pd.DataFrame) -> pd.DataFrame:
    """Get parent signature and variables in a class
    Args:
        df (pd.DataFrame): Dataset

    Returns:
        pd.DataFrame: Dataset with parent signature and variables
    """
    tqdm.pandas(desc="Adding inherit elements")
    df["inherit_elements"] = df["parent_class_code"].progress_apply(
        extract_signature_and_var
    )
    return df


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--input", dest="input")
    args.add_argument("--input-type", dest="input_type")
    args.add_argument("--output", dest="output")
    args.add_argument("--checkpoint", dest="checkpoint")
    args.add_argument("--dir", dest="dir")
    args = args.parse_args()
    match args.input_type:
        case "jsonl":
            df = pd.read_json(args.input, lines=True)
        case "parquet":
            df = pd.read_parquet(args.input, "fastparquet")
        case "csv":
            df = pd.read_csv(args.input)
    df = df.loc[501:1000]   # Temporary add
    print("Read dataset done")
    df = add_parent_class_code(df=df, storage_url=args.dir)
    print("Add parent class code done")
    # df.to_parquet(args.checkpoint, "fastparquet")
    df = get_parent_signature_and_var(df=df)
    print("Add inherit elements done")
    # df.to_parquet(args.output, "fastparquet")
    df.to_csv(args.output)
if __name__ == "__main__":
    main()
