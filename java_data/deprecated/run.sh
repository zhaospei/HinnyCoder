# Run get compiler feedback

python /var/data/lvdthieu/code-generation/java_data/deprecated/get_compiler_feedback.py \
    --input /var/data/lvdthieu/test_finetune.parquet \
    --input-type parquet \
    --output /var/data/lvdthieu/test_finetune_compiled.parquet \
    --dir /var/data/lvdthieu/repos/processed-projects \
    --tmp /var/data/lvdthieu/repos/tmp \
    --col generated_code \
    --mvn /var/data/lvdthieu/apache-maven-3.6.3/bin/mvn \
    --logfile /var/data/lvdthieu/error.log