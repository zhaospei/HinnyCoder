from java.java8.JavaLexer import JavaLexer
from antlr4 import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from subprocess import run
from collections import Counter
import os
from tqdm import tqdm

def count_java_tokens_antlr4(code):
    lexer = JavaLexer(InputStream(code))
    token_count = 0
    for token in lexer.getAllTokens():
        token_count += 1
    return token_count


def cr_and_num_token(dataset_url: str, compile_info_col: str):
    df = pd.read_parquet(dataset_url, "fastparquet")
    df["len_func_body"] = df["func_body"].apply(lambda func: count_java_tokens_antlr4(func))
    print(df["len_func_body"].describe())
    from collections import defaultdict
    buckets = [(3, 10), (10, 33), (33, 50), (50, 102), (102, 200), (200, 400), (400, 800), (800, 1300)]
    stats = {}
    for _, row in df.iterrows():
        for bucket in buckets:
            if row["len_func_body"] >= bucket[0] and row["len_func_body"] < bucket[1]:
                tmp = stats.get(bucket, [0, 0])
                tmp[0] += 1
                if row[compile_info_col] == "<COMPILED_SUCCESSFULLY>":
                    tmp[1] += 1
                stats[bucket] = tmp
                break
    # Data
    intervals = [str(bucket) for bucket in buckets]
    compilables = [stats[bucket][1] for bucket in buckets]
    totals = [stats[bucket][0] for bucket in buckets]
    percentages = [stats[bucket][1] / stats[bucket][0] * 100 for bucket in buckets]
    # Plot
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    bar_width = 0.35
    x = np.arange(len(intervals))

    bars1 = ax1.bar(x - bar_width/2, compilables, bar_width, color='skyblue', label='#Compilable')
    bars2 = ax1.bar(x + bar_width/2, totals, bar_width, color='orange', label='#Func')
    # Add percentages above each column
    for bar, compilable in zip(bars1, compilables):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, compilable, ha='center')

    # Add values above each column in the additional column
    for bar, value in zip(bars2, totals):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, value, ha='center', color='black')
    
    ax2.plot(x, percentages, marker='o', color='blue', label='Percentage', linestyle='-')
    for i, percentage in enumerate(percentages):
        ax2.text(i, percentage, f'{percentage:.2f}%', ha='right', va='bottom')
        
    ax1.set_xlabel('Function Body Length')
    ax1.set_ylabel('Compilable / Num_Func')
    ax2.set_ylabel('Percentage')
    plt.title('Distribution')
    ax1.set_xticks(x, intervals, rotation=45, ha='right')
    ax1.legend(loc="center right")
    ax1.set_ylim(0, max(max(compilables), max(totals)) + 100)
    ax2.set_ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


def check_compilable_rate(dataset_url: str, compile_info_col: str="compile_info_filled_file_baseline_output") -> int:
    import pandas as pd
    df = pd.read_parquet(dataset_url, "fastparquet")
    return len(df[df[compile_info_col] == "<COMPILED_SUCCESSFULLY>"]) / len(df)


def jsonl2parquet(src: str, dst: str):
    import pandas as pd
    df = pd.read_json(src, lines=True)
    print(df.info())
    df.to_parquet(dst, "fastparquet")


from extract_parent_context import extract_signature_and_var

java_code = """
public class Test {
    public static void main(String[] args) {
        int a = 10;
        int b = 20;
        int c = a + b;
    }
}

public class Test2 {
    public static void main(String[] args) {
        int a = 10;
        int b = 20;
        int c = a + b;
    }
}
"""

# print(extract_signature_and_var(java_code))
def checker(repo_storage: str, ext: str):
    class_files = []
    for path, dir, files in os.walk(repo_storage):
        for name in files:
            if "$" not in name:
                class_files.append("{}/{}".format(path,name))
    class_files = list(filter(lambda file_path: "target/classes" in file_path, class_files))
    print(len(class_files))
    java_files = [lambda class_file: class_file.replace("target/classes", "src/main/java").replace(".class", ".java"), class_files]
    print(*java_files[:5], sep='\n')
    correct_java_files = []
    for java_file in java_files:
        try:
            if os.path.exists(java_file):
                correct_java_files.append(java_file)
        except Exception as e:
            print(e.message)
            print(java_file)
            break
    print(len(correct_java_files))
    print(*correct_java_files[:10], sep='\n')
        

def check_dup():
    new_projects = os.listdir("/var/data/lvdthieu/repos/new-projects")
    new_projects = [p.split('/')[-1] for p in new_projects]
    with open("/var/data/lvdthieu/projects.txt", "r") as f:
        old_projects = f.read().split('\n')[:-1]
    print(new_projects[:5])
    print("-" * 100)
    print(old_projects[:-5])
    print("-"* 100)
    for p in new_projects:
        if p in old_projects:
            print(p)


def rm_dup():
    new_projects = os.listdir("/var/data/lvdthieu/repos/new-projects")
    with open("/var/data/lvdthieu/projects.txt", "r") as f:
        old_projects = f.read().split('\n')[:-1]
    for p in new_projects:
        if p in old_projects:
            cmd=f"""
            cd /var/data/lvdthieu/repos/new-projects            
            rm -rf {p}
            """
            run(cmd, shell=True)
            print(f"Deleted {p}")


def get_java_file():
    os.chdir("/var/data/lvdthieu/repos/processed-projects")
    all_files = []
    for p in os.listdir():
        cmd = f"""
        find {p} -name *.java
        """
        data = run(cmd, shell=True, text=True, capture_output=True)
        if data.stdout:
            files = data.stdout.split('\n')
            print(f"{p}: {len(files)}")
            all_files.extend(files)
    print("# files:", len(all_files))
    df = pd.DataFrame({"java_files": all_files})
    df.to_parquet("/var/data/lvdthieu/java-files.parquet", "fastparquet")


def filter1():
    df = pd.read_parquet("/var/data/lvdthieu/java-files.parquet", "fastparquet")
    df = df[~df["java_files"].str.contains("test")]
    df.to_parquet("/var/data/lvdthieu/old.parquet", "fastparquet")


def filter2():
    df = pd.read_parquet("/var/data/lvdthieu/old.parquet", "fastparquet")
    df = df[df["java_files"].str.contains("src/main/java")]
    df.to_parquet("/var/data/lvdthieu/old1.parquet", "fastparquet")


def filter3():
    """Remove java file without correspoding class file because it means that the file is not compiled
    """
    df = pd.read_parquet("/var/data/lvdthieu/old1.parquet")
    valid_java_files = []
    for file in tqdm(df["java_files"].tolist(), desc="Filtering"):
        class_path = file.replace("/src/main/java", "/target/classes").replace(".java", ".class")
        if os.path.exists(f"/var/data/lvdthieu/repos/processed-projects/{class_path}"):
            valid_java_files.append(file)
    print(len(valid_java_files))
    new_df = pd.DataFrame({"java_files": valid_java_files})
    new_df.to_parquet("/var/data/lvdthieu/old2.parquet", "fastparquet")
    new_df = new_df.sample(n=100, random_state=0)
    new_df.to_csv("/var/data/lvdthieu/java-files-check-v2.csv")


def restruct():
    """Restruct dataset of java file for dividing information into fields
    """
    df = pd.read_parquet("/var/data/lvdthieu/old2.parquet", "fastparquet")
    tqdm.pandas(desc="Splitting")
    def func(url):
        parts = url.split('/')
        project_name = parts[0]
        relative_path = '/'.join(parts[1:])
        return project_name, relative_path
    
    df["proj_name"], df["relative_path"] = zip(*df["java_files"].progress_apply(func))
    print(df.info())
    print("-"* 100)
    print(df.describe())
    df.to_parquet("/var/data/lvdthieu/old3.parquet", "fastparquet")


def normalize():
    df = pd.read_parquet("/var/data/lvdthieu/old3.parquet", "fastparquet")
    cnt = Counter(df["proj_name"].tolist())
    new = pd.DataFrame({"java_files": [], "proj_name": [], "relative_path": []})
    for p in cnt:
        print(p)
        if cnt[p] <= 1256:
            new = pd.concat([new, df[df["proj_name"] == p]], axis="index")
        else:
            tmp = df[df["proj_name"] == p]
            tmp = tmp.sample(n=1256)
            new = pd.concat([new, tmp], axis="index")
    new.to_parquet("/var/data/lvdthieu/old4.parquet", "fastparquet")


def split_projects(input_path, storage_url):
    import json
    with open(input_path, "r") as f:
        projects = json.load(f)
    print(len(projects))
    for project in projects:
        project_name = project.split('/')[-1]
        with open(f"{storage_url}/{project_name}.json", "w") as f:
            json.dump({project: projects[project]}, f)


if __name__ == "__main__":
    # processed_project = "/var/data/lvdthieu/repos/processed-projects"
    # checker(processed_project, ".class")
    # get_java_file()
    # filter1()
    # filter2()
    # filter3()
    # restruct()
    # normalize()
    split_projects("/var/data/lvdthieu/projects-v1.json", "/var/data/lvdthieu/code-generation/java_data/data/parsed")

df1 = newdf[newdf["len_func_body"] > 1]