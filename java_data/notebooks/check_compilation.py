import subprocess
from tqdm import tqdm
import pandas as pd
import multiprocessing
df = pd.read_parquet("/home/hieuvd/lvdthieu/adapt_defects4j_filtered.parquet")
projects = df["proj_name"].unique()
for project in projects:
    repo = project.split('_')[1]
    cmd = f"""
    /data/hieuvd/lvdthieu/defects4j/framework/bin/defects4j \
    compile \
    -w /data/hieuvd/lvdthieu/defects4j/data/{project}/{repo} \
    """
    try:
        res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        print(f"Run {project}:", res.stderr)
    except:
        print(f"error when run {project}")