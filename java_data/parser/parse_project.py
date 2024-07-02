import logging
from multiprocessing import Pool
from subprocess import PIPE, Popen, run
from typing import List

import pandas as pd
from tqdm import tqdm

base_dir = "/data/hieuvd/lvdthieu/repos/processed-projects"
parse_project = "/home/hieuvd/lvdthieu/parse_project"
# projects = [
#     "PlexPt_chatgpt-java",
#     "Pay-Group_best-pay-sdk",
#     "eirslett_frontend-maven-plugin",
#     "obsidiandynamics_kafdrop",
#     "DerekYRC_mini-spring",
#     "houbb_sensitive-word",
#     "google_truth",
#     "joelittlejohn_jsonschema2pojo",
#     "Kong_unirest-java",
#     "qiujiayu_AutoLoadCache",
#     "ainilili_ratel",
#     "logfellow_logstash-logback-encoder",
#     "elunez_eladmin",
#     "PlayEdu_PlayEdu",
#     "javamelody_javamelody",
#     "subhra74_snowflake",
#     "jeecgboot_jeecg-boot",
#     "mapstruct_mapstruct",
#     "spring-cloud_spring-cloud-gateway",
#     "docker-java_docker-java",
#     "YunaiV_ruoyi-vue-pro",
#     "zhkl0228_unidbg",
#     "pmd_pmd",
#     "graphhopper_graphhopper",
#     "jitsi_jitsi",
#     "orientechnologies_orientdb",
# ]

# projects = [
#     "spring-cloud_spring-cloud-kubernetes"
# ]
finetune = pd.read_parquet("/home/hieuvd/lvdthieu/new_finetune.parquet")
projects = finetune["proj_name"].unique().tolist()
class_path = "." f":'{parse_project}/target/dependency/*'"


def processor(args):
    projects, index = args
    logger = logging.Logger(f"parse-project_{index}", logging.INFO)
    logger.addHandler(
        logging.FileHandler(f"/home/hieuvd/lvdthieu/parse-project_{index}.log")
    )
    for project in tqdm(
        projects, total=len(projects), desc=f"Proc {index}", position=index
    ):
        cmd = (
            f"cd {parse_project}/target/classes "
            f"&& java -cp {class_path} "
            "Main "
            f"{base_dir} "
            f"{project}"
        )
        try:
            result = run(cmd, shell=True, text=True, capture_output=True)
            logger.info(result.stderr)
        except:
            print("<encounter_error>", project)


batch_size = 10
num_process = (
    len(projects) // batch_size
    if len(projects) % batch_size == 0
    else len(projects) // batch_size + 1
)
subsets = [
    (projects[i : i + batch_size], i // batch_size)
    for i in range(0, len(projects), batch_size)
]


with Pool(num_process) as p:
    p.map(processor, subsets)
