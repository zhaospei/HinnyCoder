import logging
import os
import subprocess

import pandas as pd
from tqdm import tqdm

JUNIT = "/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/junit-4.12.jar"
HAMCREST = "/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/hamcrest-core-1.3.jar"
EVOSUITE = "/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/lib/evosuite-1.0.6.jar"
RANDOOP = "/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/lib/randoop-4.3.3/randoop-all-4.3.3.jar"
RANDOOP_TEST_BASE = "/data/hieuvd/lvdthieu/repos/randoop"
EVOSUITE_TEST_BASE = "/data/hieuvd/lvdthieu/repos/evosuite"


logger = logging.getLogger()
logger.addHandler(
    logging.FileHandler("/home/hieuvd/lvdthieu/run_test_evosuite_52.log")
)
logger.setLevel(logging.INFO)


input_url = "/home/hieuvd/lvdthieu/valid_evosuite_52.parquet"
output_url = "/home/hieuvd/lvdthieu/valid_evosuite_52.parquet"

df = pd.read_parquet(input_url, "fastparquet")
base_dir = "/data/hieuvd/lvdthieu/repos/tmp-projects"
return_codes = []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Evosuite"):
    test_dir = f"{EVOSUITE_TEST_BASE}/{row['proj_name']}/{row['relative_path'].replace('.java', '')}/evosuite-tests"
    class_to_test = (
        row["relative_path"]
        .split("src/main/java/")[1]
        .replace(".java", "")
        .replace("/", ".")
    )
    rev_path = "/".join(class_to_test.split(".")[:-1])
    target_dir = (
        f"{base_dir}/{row['proj_name']}/"
        f"{row['relative_path'].split('src/main/java/')[0]}/target"
    )
    if not os.path.exists(target_dir):
        jar = ""
    else:
        for item in os.listdir(target_dir):
            if item.endswith("jar-with-dependencies.jar"):
                jar = f"{target_dir}/{item}"
                break
        else:
            jar = f"{target_dir}/classes"
    class_test = f"{class_to_test}_ESTest"
    cmd = (
        f"javac -cp {jar}:{EVOSUITE}:{HAMCREST}:{JUNIT} {test_dir}/{rev_path}/*.java "
        f"&& cd {test_dir} "
        f"&& java -cp .:{jar}:{EVOSUITE}:{HAMCREST}:{JUNIT} org.junit.runner.JUnitCore {class_test}"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    # subprocess.run(cmd, shell=True)
    if result.returncode == 0:
        return_codes.append(True)
        logger.info(
            "{:<30} {}".format("All thing look good", row["relative_path"])
        )
    else:
        if "FAILURES!!!" in result.stdout:
            return_codes.append(True)
            logger.warning(
                "{:<30} {}".format("Some test fail", row["relative_path"])
            )
        else:
            return_codes.append(False)
            logger.error(
                "{:<30} {}".format("Can not run test", row["relative_path"])
            )

df["runnable"] = return_codes
df.to_parquet(output_url, "fastparquet")
print("Success:", sum(return_codes), "/", len(return_codes))
