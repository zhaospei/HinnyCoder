"""Run maven
"""

import logging
import subprocess

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger()
logger.addHandler(logging.FileHandler("/var/data/lvdthieu/maven26.log"))
logger.setLevel(logging.INFO)

test = pd.read_parquet(
    "/var/data/lvdthieu/HinnyCoder/java_data/data/tmp/rambo_upperbound.parquet"
)
test_projects = test["proj_name"].unique()
test_projects = ["docker-java_docker-java"]

for project in tqdm(
    test_projects, total=len(test_projects), desc="Compiling projects"
):
    REPO = "_".join(project.split("_")[1:])

    cmd = (
        f"cd /var/data/lvdthieu/repos/processed-projects/{project}/{REPO} "
        + "&& /var/data/lvdthieu/apache-maven-3.6.3/bin/mvn clean compile"
    )
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to compile {project}")
    else:
        logger.info(f"Compiled {project}")

# -DskipTests -Dcheckstyle.skip -Dgpg.skip=true -Dlicense.skip=true
