python /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/randoop.py \
        --input /home/hieuvd/lvdthieu/error_samples.parquet \
        --output /home/hieuvd/lvdthieu/error_samples_randoop.parquet \
        --base-dir /data/hieuvd/lvdthieu/repos/tmp-projects \
        --time-limit 30 \
        --randoop /home/hieuvd/lvdthieu/code-generation/java_data/processors/test_generator/lib/randoop-4.3.3/randoop-all-4.3.3.jar \
        --output-dir /data/hieuvd/lvdthieu/repos/randoop \
        --log-dir /home/hieuvd/lvdthieu/log_randoop_error_samples \
        --proc 5
