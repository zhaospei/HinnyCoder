python /home/hieuvd/lvdthieu/code-generation/java_data/processors/parser/parse_func.py \
    --input /home/hieuvd/lvdthieu/170724_500_similar_method.parquet \
    --output /home/hieuvd/lvdthieu/170724_500_similar_method_re.parquet \
    --base-dir /data/hieuvd/lvdthieu/repos/processed-projects \
    --parse-function /home/hieuvd/lvdthieu/code-generation/java_data/parse_function \
    --generated-col similar_method_output \
    --num-proc 1 \
    --log-dir "/home/hieuvd/lvdthieu/log_parse_func"
