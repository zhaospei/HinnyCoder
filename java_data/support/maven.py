"""Run maven
"""

import logging
import subprocess

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger()
logger.addHandler(logging.FileHandler("/home/hieuvd/lvdthieu/maven26.log"))
logger.setLevel(logging.INFO)

test = pd.read_parquet("/home/hieuvd/lvdthieu/170724_500_similar_method.parquet")
test_projects = test["proj_name"].unique()

for project in tqdm(
    test_projects, total=len(test_projects), desc="Compiling projects"
):
    REPO = "_".join(project.split("_")[1:])

    cmd = (
        f"cd /data/hieuvd/lvdthieu/repos/tmp-projects/{project}/{REPO} "
        + "&& /home/hieuvd/apache-maven-3.6.3/bin/mvn clean compile -DskipTests -Dcheckstyle.skip -Dgpg.skip=true -Dlicense.skip=true"
    )
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to compile {project}")
    else:
        logger.info(f"Compiled {project}")
    
