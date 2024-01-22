DATA_PATH="zhaospei/smart-contract-gen"
OUTPUT_PATH="tmp/deepspeed-09-01/"
MODEL_PATH="deepseek-ai/deepseek-coder-6.7b-base"

DS_SKIP_CUDA_CHECK=1 deepspeed finetune_deepseek.py \
    --model_name_or_path $MODEL_PATH \
    --data_path $DATA_PATH \
    --output_dir $OUTPUT_PATH \
    --num_train_epochs $1 \
    --model_max_length 2048 \
    --per_device_train_batch_size $2 \
    --per_device_eval_batch_size 1 \
    --gradient_accumulation_steps 4 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 100 \
    --save_total_limit 100 \
    --learning_rate 2e-5 \
    --warmup_steps 10 \
    --logging_steps 1 \
    --lr_scheduler_type "cosine" \
    --gradient_checkpointing True \
    --report_to "tensorboard" \
    --deepspeed configs/ds_config_zero3.json \
    --bf16 True
