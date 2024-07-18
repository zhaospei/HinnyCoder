python /home/hieuvd/lvdthieu/HinnyCoder/java_data/processors/parser/extract_initial_context.py \
    --input /home/hieuvd/lvdthieu/new_500_initial_context.parquet \
    --output /home/hieuvd/lvdthieu/new_500_initial_context.parquet\
    --parser /home/hieuvd/lvdthieu/HinnyCoder/java_data/extract_initial_context \
    --base-dir /data/hieuvd/lvdthieu/repos/processed-projects \
    --json-dir /home/hieuvd/lvdthieu/parsed_test \
    --num-proc 1 \
    --log-dir /home/hieuvd/lvdthieu/log_extract_initial_context \
    --task param
