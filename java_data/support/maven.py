"""Run maven
"""

import logging
from subprocess import run

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger()
logger.addHandler(logging.FileHandler("/home/hieuvd/lvdthieu/maven26.log"))
logger.setLevel(logging.INFO)

test = pd.read_parquet("/home/hieuvd/lvdthieu/500_parent_class_output_re.parquet")
test_projects = test["proj_name"].unique()
# test_projects = [
#     'bastillion-io_Bastillion',
#     'PlayEdu_PlayEdu',
#     'Col-E_Recaf',
#     'knowm_XChange',
#     'citerus_dddsample-core',
#     'DependencyTrack_dependency-track',
#     'apache_hertzbeat',
#     'iluwatar_java-design-patterns',
#     'bytedeco_javacv',
#     'jeecgboot_jeecg-boot',
#     'jitsi_jitsi',
#     'joelittlejohn_jsonschema2pojo',
#     'obsidiandynamics_kafdrop',
#     'mabe02_lanterna',
#     'redis_lettuce',
#     'logfellow_logstash-logback-encoder',
#     'gz-yami_mall4cloud',
#     'gz-yami_mall4j',
#     'tonikelope_megabasterd',
#     'zlt2000_microservices-platform',
#     'novicezk_midjourney-proxy',
#     '201206030_novel',
#     'pac4j_pac4j',
#     'pig-mesh_pig',
#     'shopizer-ecommerce_shopizer',
#     'SonicCloudOrg_sonic-agent',
#     'soot-oss_soot',
#     'xuchengsheng_spring-reading',
#     'spring-projects_spring-retry',
#     'xerial_sqlite-jdbc',
#     '88250_symphony',
#     'bonigarcia_webdrivermanager'
# ]
# test_projects = [
#     "qiujiayu_AutoLoadCache",
#     "speedment_speedment",
#     "lukas-krecan_ShedLock",
#     "ulisesbocchio_jasypt-spring-boot"
# ]
test_projects = test_projects[21:]

for project in tqdm(
    test_projects, total=len(test_projects), desc="Compiling projects"
):
    REPO = "_".join(project.split("_")[1:])

    cmd = (
        f"cd /data/hieuvd/lvdthieu/repos/tmp-projects/{project}/{REPO} "
        + "&& /home/hieuvd/apache-maven-3.6.3/bin/mvn clean compile -DskipTests -Dcheckstyle.skip -Dgpg.skip=true -Dlicense.skip=true"
    )
    
    result = run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to compile {project}")
    else:
        logger.info(f"Compiled {project}")
    
