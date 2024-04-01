import copy
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Sequence

import torch
import torch.distributed
import transformers
from transformers import Trainer
from datasets import load_dataset
import argparse
from contextlib import nullcontext
from model import DataCollatorForDualObjectiveDataset, DualObjectiveTrainer

BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
SIGN_BEGIN_TOKEN = "<sign_begin>"
SIGN_END_TOKEN = "<sign_end>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"

def build_signature_func(instruction: str):
    return SIGN_BEGIN_TOKEN + instruction + SIGN_END_TOKEN

def deepseek_build_output_compiler(output: str):
    output = output.replace('<COMPILED_SUCCESSFULLY>', 'success')
    # output = ' '.join(output.split()[:30])
    return output

def deepseek_build_masked_func(masked_func: str):
    masked_func = masked_func.replace('<FILL_FUNCTION_BODY>', FILL_TOKEN)
    return BEGIN_TOKEN + masked_func + END_TOKEN

def codellama_build_masked_func(masked_func):
    prefix_tokens, suffix_tokens = masked_func.split('<FILL_FUNCTION_BODY>')
    return '▁<PRE>' + prefix_tokens + '▁<SUF>' + suffix_tokens + '▁<MID>'

@dataclass
class ModelArguments:
    model_name_or_path: Optional[str] = field(default="deepseek-ai/deepseek-coder-6.7b-instruct")

@dataclass
class DataArguments:
    data_path: str = field(default=None, metadata={"help": "Path to the training data."})


@dataclass
class TrainingArguments(transformers.TrainingArguments):
    cache_dir: Optional[str] = field(default=None)
    optim: str = field(default="adamw_torch")
    model_max_length: int = field(
        default=512,
        metadata={"help": "Maximum sequence length. Sequences will be right padded (and possibly truncated)."},
    )

def safe_save_model_for_hf_trainer(trainer: transformers.Trainer, output_dir: str):
    """Collects the state dict and dump to disk."""
    state_dict = trainer.model.state_dict()
    if trainer.args.should_save:
        cpu_state_dict = {key: value.cpu() for key, value in state_dict.items()}
        del state_dict
        trainer._save(output_dir, state_dict=cpu_state_dict)  # noqa


def _tokenize_fn(strings: Sequence[str], tokenizer: transformers.PreTrainedTokenizer) -> Dict:
    """Tokenize a list of strings."""
    tokenized_list = [
        tokenizer(
            text,
            return_tensors="pt",
            padding="longest",
            max_length=tokenizer.model_max_length,
            truncation=True,
        )
        for text in strings
    ]

    input_ids = labels = [tokenized.input_ids[0] for tokenized in tokenized_list]
    input_ids_lens = labels_lens = [
        tokenized.input_ids.ne(tokenizer.pad_token_id).sum().item() for tokenized in tokenized_list
    ]

    return dict(
        input_ids=input_ids,
        labels=labels,
        input_ids_lens=input_ids_lens,
        labels_lens=labels_lens,
    )


def preprocess(
    sources: Sequence[str],
    targets: Sequence[str],
    tokenizer: transformers.PreTrainedTokenizer,
) -> Dict:
    """Preprocess the data by tokenizing."""
    examples = [s + t for s, t in zip(sources, targets)]
    examples_tokenized, sources_tokenized = [_tokenize_fn(strings, tokenizer) for strings in (examples, sources)]
    input_ids = examples_tokenized["input_ids"]

    labels = copy.deepcopy(input_ids)
    for label, source_len in zip(labels, sources_tokenized["input_ids_lens"]):
        label[:source_len] = IGNORE_INDEX
    return dict(input_ids=input_ids, labels=labels)
   

def func_tokenize_function(examples, tokenizer):
    sources = [build_signature_func(instruction) for instruction in examples['deepseek_output']]
    targets = [f"{output}\n{EOT_TOKEN}" for output in examples['signature_only']]

    data_dict = preprocess(sources, targets, tokenizer)
    return data_dict

def class_tokenize_function(examples, tokenizer):
    sources = [
        deepseek_build_masked_func(instruction) + '\n<ouput>\n' + output + '\n<compile>\n' + deepseek_build_output_compiler(compile_info) + '\n<inherit>\n' + inherit_elements + '\n<correct> '
        for (instruction, output, compile_info, inherit_elements) in zip(examples['masked_contract'], examples['deepseek_output'], examples['compile_info'], examples['inherit_elements'])
    ]
    targets = [f"{output}\n{EOT_TOKEN}" for output in examples['func_body']]
    data_dict = preprocess(sources, targets, tokenizer)
    return data_dict

def step2_train_tokenize_function(examples, tokenizer):
    func_data_dict = func_tokenize_function(examples, tokenizer)
    class_data_dict = class_tokenize_function(examples, tokenizer)

    return dict(
        func_input_ids=func_data_dict['input_ids'],
        func_labels=func_data_dict['labels'],
        class_input_ids=class_data_dict['input_ids'],
        class_labels=class_data_dict['labels']
    )

    

def train(args):
    
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        args.model_name_or_path,
        model_max_length=args.model_max_length,
        padding_side="right",
        use_fast=True,
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
        load_in_8bit=args.load_in_8bit,
    )

    print("Load model from {} over.".format(args.model_name_or_path))

    raw_train_datasets = load_dataset(
        args.data_path,
        split=args.data_split,
    )

    train_dataset = raw_train_datasets.map(
        step2_train_tokenize_function,
        batched=True,
        batch_size=3000,
        num_proc=32,
        remove_columns=raw_train_datasets.column_names,
        load_from_cache_file=True, # not args.overwrite_cache
        desc="Running Encoding",
        fn_kwargs={ "tokenizer": tokenizer}
    )

    data_collator = DataCollatorForDualObjectiveDataset(tokenizer=tokenizer)

    def create_peft_config(model):
        from peft import (
            get_peft_model,
            LoraConfig,
            TaskType,
            prepare_model_for_kbit_training,
        )

        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=8,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules = ["q_proj", "v_proj"]
        )

        # prepare int-8 model for training
        if args.load_in_8bit:
            model = prepare_model_for_kbit_training(model)
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
        return model, peft_config

    # create peft config
    model, lora_config = create_peft_config(model)

    output_dir = args.output_dir

    config = {
        'lora_config': lora_config,
        'learning_rate': 2e-5,
        'num_train_epochs': args.epochs,
        'gradient_accumulation_steps': 2,
        'per_device_train_batch_size': args.batch_size,
        'gradient_checkpointing': False,
    }

    model.train()


    # Define training args
    training_args = transformers.TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        bf16=True,  # Use BF16 if available
        # logging strategies
        logging_dir=f"{output_dir}/logs",
        logging_strategy="steps",
        logging_steps=10,
        save_strategy="no",
        optim="adamw_torch",
        max_steps= -1,
        **{k:v for k,v in config.items() if k != 'lora_config'}
    )

    # profiler = nullcontext()
    # with profiler:
        # Create Trainer instance
    trainer = DualObjectiveTrainer(
        alpha=args.alpha,
        output_function=args.output_function,
        model=model,
        args=training_args,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        data_collator=data_collator,
        eval_dataset=None,
    )

    # Start training
    # if args.task == 'train': 
    trainer.train()

    model.save_pretrained(training_args.output_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch_size", default=1, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_name_or_path", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--data_path", type=str, default='zhaospei/refine-v2')
    parser.add_argument("--output_file", type=str, default="gen.output")
    parser.add_argument("--output_dir", type=str, default='model')
    parser.add_argument("--model_max_length", type=int, default=2100)
    parser.add_argument("--data_split", type=str, default='train')
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument('--output_function', action='store_true')

    args = parser.parse_args()
    
    train(args)

if __name__ == "__main__":
    main()