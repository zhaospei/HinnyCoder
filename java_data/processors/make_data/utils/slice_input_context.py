import os
import re
import sys
from typing import List, NamedTuple, Optional, Tuple

import pandas as pd
from antlr4 import *

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/..")
from java.java8.JavaLexer import JavaLexer
from java.java8.JavaParser import JavaParser
from java.java8.JavaParserListener import JavaParserListener
from tqdm import tqdm

df = pd.read_parquet("/home/hieuvd/lvdthieu/adapt_defects4j_filtered.parquet")


class Location(NamedTuple):
    start_line: int
    start_col: int
    end_line: int
    end_col: int


def get_location(java_code: str, loc: Location) -> Tuple[int, int]:
    java_code = java_code.replace("\r\n", "\n")
    lines = java_code.split("\n")
    start_idx = 0
    for i in range(loc.start_line - 1):
        start_idx += len(lines[i])
    start_idx = start_idx + loc.start_col + loc.start_line - 1

    end_idx = 0
    for i in range(loc.end_line - 1):
        end_idx += len(lines[i])
    end_idx = end_idx + loc.end_col + loc.end_line - 1
    return java_code, start_idx, end_idx


class Visitor(JavaParserListener):
    def __init__(self, java_code, target_method):
        super().__init__()
        self.java_code = java_code
        self.target_method = target_method
        self.found_method = None

    def enterClassDeclaration(self, ctx):
        body = ctx.classBody().block()
        body_loc = Location(
            body.start.line,
            body.start.column,
            body.stop.line,
            body.stop.column + len(body.stop.text)
        )
        body_loc 

    def enterMethodDeclaration(self, ctx):
        func_name = ctx.identifier().getText()
        
        body = ctx.methodBody().block()
        func_loc = Location(
            ctx.start.line,
            ctx.start.column,
            ctx.stop.line,
            ctx.stop.column + len(ctx.stop.text),
        )
        if body:
            body_loc = Location(
                body.start.line,
                body.start.column,
                body.stop.line,
                body.stop.column + len(body.stop.text)
            )
            java_code, func_start, func_end = get_location(
                self.java_code, func_loc
            )

            java_code, body_start, body_end = get_location(
                self.java_code, body_loc
            )

            if func_name == self.target_method:
                print("Found")
                print(java_code[func_start:func_end])


def parse(java_code: str, target_method: str):
    # try:
    input_stream = InputStream(java_code)
    lexer = JavaLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParser(token_stream)
    tree = parser.compilationUnit()
    # Create listener
    listener = Visitor(java_code, target_method)
    # Walk the parse tree
    walker = ParseTreeWalker()
    walker.walk(listener, tree)


# except Exception:
#     return None

# parse(df.at[0, "masked_class"], df.at[0, "func_name"])
# print(df.at[0, "function_signature"])
with open("/home/hieuvd/lvdthieu/HinnyCoder/java_data/processors/make_data/utils/tmp.java", 'w', encoding="utf-8", errors="ignore") as f:
    f.write(df.at[1, "masked_class"])