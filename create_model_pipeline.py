import copy
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Sequence
from peft import PeftModel

import torch
import torch.distributed
import transformers
from transformers import Trainer
from datasets import load_dataset
import argparse
from contextlib import nullcontext

from transformers import (
    AutoModelForCausalLM, 
    CodeLlamaTokenizer,
    default_data_collator, 
    Trainer, 
    TrainingArguments,
    TrainerCallback,
    BitsAndBytesConfig,
    AutoTokenizer,
)

import bitsandbytes as bnb


BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"

def train(args):
    
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        trust_remote_code=True
    )

    if 'codellama' in args.model_name_or_path:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    print(tokenizer)

    print("PAD Token:", tokenizer.pad_token, tokenizer.pad_token_id)
    print("BOS Token", tokenizer.bos_token, tokenizer.bos_token_id)
    print("EOS Token", tokenizer.eos_token, tokenizer.eos_token_id)

    print("Load tokenizer from {} over.".format(args.model_name_or_path))

    model = transformers.AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )


    model = PeftModel.from_pretrained(model, args.model_peft)
    model = model.merge_and_unload()

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, 
                                            trust_remote_code=True,
                                            )

    print('int8 done.')
    model.push_to_hub(args.hub_model_path)
    tokenizer.push_to_hub(args.hub_model_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--model_peft", type=str, default='')
    parser.add_argument("--hub_model_path", type=str, default='')
    args = parser.parse_args()
    train(args)

if __name__ == "__main__":
    main()
