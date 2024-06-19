import argparse
import logging
import os
from collections import Counter
from subprocess import run
from typing import List

import pandas as pd
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--dir", dest="dir")
parser.add_argument("--output", dest="output")


def get_java_file_urls(dir: str) -> List[str]:
    os.chdir(dir)
    all_files = []
    for p in os.listdir():
        cmd = f"""
        find {p} -name *.java
        """
        data = run(cmd, shell=True, text=True, capture_output=True)
        if data.stdout:
            files = data.stdout.split("\n")
            print(f"{p}: {len(files)}")
            all_files.extend(files)
    return all_files


def filter_url(base_dir: str, java_file_urls: List[str]) -> List[str]:
    """Filter invalid java url"""
    # url not contain "test"
    java_file_urls = list(filter(lambda url: "test" not in url, java_file_urls))
    print("Length after filter 1:", len(java_file_urls))

    # url must contain "src/main/java"
    java_file_urls = list(
        filter(lambda url: "src/main/java" in url, java_file_urls)
    )
    print("Length after filter 2:", len(java_file_urls))

    # java file must have corresponding class (mean that file is compiled)
    valid_java_files = []
    for url in tqdm(java_file_urls):
        class_path = url.replace("/src/main/java", "/target/classes").replace(
            ".java", ".class"
        )
        if os.path.exists(f"{base_dir}/{class_path}"):
            valid_java_files.append(url)
    print("Length after filter 3:", len(valid_java_files))
    return valid_java_files


def construct_df(java_file_urls: List[str]) -> pd.DataFrame:
    """Dividing java file urls into fields"""

    def func(url):
        parts = url.split("/")
        project_name = parts[0]
        relative_path = "/".join(parts[1:])
        return project_name, relative_path

    df = pd.DataFrame()
    df["java_file_urls"] = java_file_urls
    df["proj_name"], df["relative_path"] = zip(
        *df["java_file_urls"].apply(func)
    )
    print(df.info())
    print("-" * 100)
    print(df.describe())
    return df


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    cnt = Counter(df["proj_name"].tolist())
    new = pd.DataFrame(
        {"java_file_urls": [], "proj_name": [], "relative_path": []}
    )
    for p in cnt:
        print(p)
        if cnt[p] <= 1256:
            new = pd.concat([new, df[df["proj_name"] == p]], axis="index")
        else:
            tmp = df[df["proj_name"] == p]
            tmp = tmp.sample(n=1256, random_state=0)
            new = pd.concat([new, tmp], axis="index")
    new.reset_index(drop=True, inplace=True)
    return new


def main(args):
    java_file_urls = get_java_file_urls(args.dir)
    print("Total java file:", len(java_file_urls))
    java_file_urls = filter_url(args.dir, java_file_urls)
    df = construct_df(java_file_urls)
    df = normalize_df(df)
    df.to_parquet(args.output)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
