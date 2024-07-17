python /home/hieuvd/lvdthieu/code-generation/java_data/processors/parser/parse_func.py \
    --input /home/hieuvd/lvdthieu/500_parent_class_output_re.parquet \
    --output /home/hieuvd/lvdthieu/500_parent_class_output_re.parquet \
    --base-dir /data/hieuvd/lvdthieu/repos/processed-projects \
    --parse-function /home/hieuvd/lvdthieu/code-generation/java_data/parse_function \
    --generated-col func_body \
    --num-proc 1 \
    --log-dir "/home/hieuvd/lvdthieu/log_parse_func"
