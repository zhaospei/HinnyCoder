"""Module to run inference on a dataset."""

import sys
import argparse
import torch
import datasets
from tqdm import tqdm
# import logging
# logging.disable(logging.WARNING)
from peft import PeftModel
from transformers import AutoTokenizer, AutoModelForCausalLM

BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"


def deepseek_build_masked_func(masked_func: str):
    """
    Mask the function body with special tokens.
    """
    masked_func = masked_func.replace('FILL_FUNC_BODY', FILL_TOKEN)
    return BEGIN_TOKEN + masked_func + END_TOKEN

# dataset_id = args.dataset_id
model_id = 'deepseek-ai/deepseek-coder-6.7b-base'

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    load_in_8bit=True
)

model = PeftModel.from_pretrained(model, 'adapters/deepseek/finetune')

model.eval()
tokenizer.padding_side = "left" # Fix weird overflow issue with fp16 training

dataset = datasets.load_dataset('zhaospei/python-gold', split='test[:1]')

sources = [
    deepseek_build_masked_func(masked_class_with_comment)
    for masked_class_with_comment in dataset['masked_class_with_comment']
]

# batch_list = split_batch(sources, args.batch_size)
# len_batch = len(sources) // args.batch_size
for prompt in sources:
    model_inputs = tokenizer(
        prompt,
        return_tensors="pt",
        max_length=400,
        truncation=True
    )
    model_inputs = {k: v.to("cuda") for k, v in model_inputs.items()}
    
    # with torch.no_grad():
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=30,
        do_sample=True,
        num_return_sequences=2,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=32021
    )
    
    generated_texts = [tokenizer.decode(output, skip_special_tokens=True) for output in generated_ids]
    print(generated_texts)
