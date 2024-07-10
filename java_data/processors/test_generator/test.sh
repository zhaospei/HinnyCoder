# OPTION=$1
# if (( $OPTION == 1 ))
# then
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/run.py \
#         --input /home/hieuvd/lvdthieu/checkpoint.parquet \
#         --base-dir /home/hieuvd/lvdthieu/repos/processed-projects \
#         --time-limit 20 \
#         --output-limit 50 \
#         --randoop /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/lib/randoop-4.3.3/randoop-all-4.3.3.jar \
#         --output /home/hieuvd/lvdthieu/generate_status_4.parquet \
#         --start 11550 \
#         --end 12000 
# elif (( $OPTION == 2 ))
# then
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/utils/utils.py \
#         --task config-maven \
#         --input /home/hieuvd/lvdthieu/checkpoint.parquet \
#         --base-dir /home/hieuvd/lvdthieu/repos/processed-projects \
#         --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn
proj_name="qiujiayu_AutoLoadCache"
path_to_src="AutoLoadCache/autoload-cache-aop/autoload-cache-aop-aspectj"
qualified_name="com.jarvis.cache.aop.aspectj.AspectjAopInterceptor"

REPOS="/home/hieuvd/lvdthieu/repos/processed-projects"
RANDOOP="/home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/lib/randoop-4.3.3/randoop-all-4.3.3.jar"
CHECK_DIR="/home/hieuvd/lvdthieu/repos/check_randoop"

path_to_pom="${REPOS}/${proj_name}/${path_to_src}"
class_path=".:${path_to_pom}/target/classes:'${path_to_pom}/target/dependency/*':${RANDOOP}"    

cd ${path_to_pom} 
timeout 20 java -cp $class_path randoop.main.Main gentests \
        --testclass="${qualified_name}" \
        --time-limit=20 \
        --output-limit=50 \
        --junit-output-dir="${CHECK_DIR}" \
        --no-error-revealing-tests=true