python /home/hieuvd/lvdthieu/code-generation/java_data/processors/compile_executor/run.py \
    --input /home/hieuvd/lvdthieu/500_parent_class_output_re.parquet \
    --output /home/hieuvd/lvdthieu/500_parent_class_output_re_compiled.parquet \
    --col func_body \
    --base-dir /data/hieuvd/lvdthieu/repos/tmp-projects \
    --log-dir /home/hieuvd/lvdthieu/log_compile \
    --mvn /home/hieuvd/apache-maven-3.6.3/bin/mvn \
    --proc 5 \

