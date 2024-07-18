python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_executor/run.py \
    --input /home/hieuvd/lvdthieu/new_test.parquet \
    --output /home/hieuvd/lvdthieu/new_test_compiled.parquet \
    --col func_body \
    --base-dir /data/hieuvd/lvdthieu/repos/tmp-projects \
    --log-dir /home/hieuvd/lvdthieu/log_compile \
    --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
    --proc 10 \

