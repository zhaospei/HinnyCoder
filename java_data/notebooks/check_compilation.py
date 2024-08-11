import subprocess
from tqdm import tqdm
import pandas as pd
import multiprocessing
df = pd.read_parquet("/home/thieuluu/HinnyCoder/java_data/data/adapt_defects4j_filtered_prompt.parquet")
projects = df["proj_name"].unique()
for project in projects:
    repo = project.split('_')[1]
    cmd = f"""
    /home/thieuluu/defects4j/framework/bin/defects4j \
    compile \
    -w /home/thieuluu/defects4j/data/{project}/{repo} \
    """
    try:
        res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        print(f"Run {project}:", res.stderr)
    except:
        print(f"error when run {project}")