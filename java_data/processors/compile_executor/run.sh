python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_executor/run.py \
    --input /home/hieuvd/lvdthieu/500_parent_class_output_re.parquet \
    --output /home/hieuvd/lvdthieu/500_parent_class_output_re_compiled.parquet \
    --col parent_class_output \
    --base-dir /data/hieuvd/lvdthieu/repos/tmp-projects \
    --log-dir /home/hieuvd/lvdthieu/log_compile \
    --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
    --proc 5 \

# Check
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/run.py \
#     --input /home/hieuvd/lvdthieu/retry_v1.parquet \
#     --output /home/hieuvd/lvdthieu/retry_compiled.parquet \
#     --col generated_code \
#     --base-dir /home/hieuvd/lvdthieu/repos/tmp-projects \
#     --log-dir /home/hieuvd/lvdthieu/repos/log_finetune \
#     --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
#     --proc 4 \
#     --start-end 0:4


# Retry valid left
# python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_test_executor/run.py \
#     --input /home/hieuvd/lvdthieu/valid_left.parquet \
#     --output /home/hieuvd/lvdthieu/valid_left_compiled.parquet \
#     --col generated_code \
#     --base-dir /home/hieuvd/lvdthieu/repos/tmp-projects \
#     --log-dir /home/hieuvd/lvdthieu/repos/log_finetune \
#     --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
#     --proc 17 \
#     --start-end 0:17

