python /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/run.py \
    --input /home/hieuvd/lvdthieu/test_have_test.parquet \
    --output /home/hieuvd/lvdthieu/test_test_info.parquet \
    --col generated_code \
    --base-dir /data/hieuvd/lvdthieu/repos/tmp-projects \
    --test-dir /data/hieuvd/lvdthieu/repos/randoop \
    --log-dir /home/hieuvd/lvdthieu/log \
    --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
    --clover-jar /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/clover-4.5.2.jar \
    --junit-jar /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/junit-4.12.jar \
    --hamcrest-jar /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/lib/hamcrest-core-1.3.jar \
    --separator-code /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_executor/separate_pass_fail_test.py \
    --proc 10 