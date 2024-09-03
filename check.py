import logging
import subprocess

from tqdm import tqdm

logger = logging.getLogger()
logger.addHandler(
    logging.FileHandler("/var/data/lvdthieu/HinnyCoder/maven.log")
)
logger.setLevel(logging.INFO)

projects = [
    "jeecgboot_jeecg-boot",
    "graphhopper_graphhopper",
    "orientechnologies_orientdb",
    "jitsi_jitsi",
    "PlayEdu_PlayEdu",
    "pmd_pmd",
    "spring-cloud_spring-cloud-gateway",
    "YunaiV_ruoyi-vue-pro",
    "qiujiayu_AutoLoadCache",
    "docker-java_docker-java",
    "javamelody_javamelody",
    "eirslett_frontend-maven-plugin",
    "Kong_unirest-java",
    "zhkl0228_unidbg",
    "subhra74_snowflake",
    "mapstruct_mapstruct",
    "joelittlejohn_jsonschema2pojo",
    "DerekYRC_mini-spring",
    "elunez_eladmin",
    "houbb_sensitive-word",
    "logfellow_logstash-logback-encoder",
    "ainilili_ratel",
    "Pay-Group_best-pay-sdk",
    "google_truth",
    "obsidiandynamics_kafdrop",
    "PlexPt_chatgpt-java",
]

for project in tqdm(projects, total=len(projects), desc="Compiling"):
    repo = project.split("_")[1]
    cmd = f"""
    cd /var/data/lvdthieu/repos/processed-projects/{project}/{repo} && \
    /var/data/lvdthieu/apache-maven-3.6.3/bin/mvn clean compile
    """
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        logger.info(f"Failed to compile {project}")
    else:
        logger.info(f"Compiled {project}")
