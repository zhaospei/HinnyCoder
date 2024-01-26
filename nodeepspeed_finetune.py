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


BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"

def deepseek_build_masked_func(masked_func: str):
    masked_func = masked_func.replace('<FILL_FUNCTION_BODY>', FILL_TOKEN)
    return BEGIN_TOKEN + masked_func + END_TOKEN

def codellama_build_masked_func(masked_func):
    # [self.prefix_token] + prefix_tokens + [self.suffix_token] + suffix_tokens + [self.middle_token]
    # masked_func = masked_func.replace('<FILL_FUNCTION_BODY>', '<FILL_ME>')
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

@dataclass
class DataCollatorForSupervisedDataset(object):
    """Collate examples for supervised fine-tuning."""
    tokenizer: transformers.PreTrainedTokenizer

    def __call__(self, instances: Sequence[Dict]) -> Dict[str, torch.Tensor]:
        input_ids, labels = tuple([instance[key] for instance in instances] for key in ("input_ids", "labels"))
        input_ids = [torch.tensor(x) for x in input_ids]
        input_ids = torch.nn.utils.rnn.pad_sequence(
            input_ids, batch_first=True, padding_value=self.tokenizer.pad_token_id
        )
        labels = [torch.tensor(x) for x in labels]
        labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=IGNORE_INDEX)
        
        return dict(
            input_ids=input_ids,
            labels=labels,
            attention_mask=input_ids.ne(self.tokenizer.pad_token_id),
        )

def deepseek_train_tokenize_function(examples, tokenizer, task):
    if 'refine' in task:
        sources = [
            deepseek_build_masked_func(instruction) + '\n' + output + '\n<correct>'
            for (instruction, output) in zip(examples['masked_contract'], examples['deepseek_output'])
        ]
        targets = [f"{output}\n{EOT_TOKEN}" for output in examples['func_body']]
        data_dict = preprocess(sources, targets, tokenizer)
    else:
        sources = [
            deepseek_build_masked_func(instruction)
            for instruction in examples['masked_contract']
        ]
        targets = [f"{output}\n{EOT_TOKEN}" for output in examples['func_body']]
        data_dict = preprocess(sources, targets, tokenizer)
    return data_dict

def codellama_train_tokenize_function(examples, tokenizer):
    sources = [
        # codellama_build_masked_func(instruction) + '\n' + output + '\n<correct>'
        # codellama_build_masked_func(instruction)
        # for instruction in examples['masked_contract']
        codellama_build_masked_func(instruction) + '\n' + output + '\n<correct>'
        for (instruction, output) in zip(examples['masked_contract'], examples['codellama_ouput'])
    ]
    targets = [f"{output}\n▁<EOT>" for output in examples['func_body']]
    data_dict = preprocess(sources, targets, tokenizer)
    return data_dict

def train(args):
    # parser = transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))
    # model_args, data_args, training_args = parser.parse_args_into_dataclasses()

    # dataset_id = "zhaospei/smart-doc"
    # model_name_or_path = "codellama/CodeLlama-7b-hf"

    # tokenizer = CodeLlamaTokenizer.from_pretrained(model_name_or_path)

    # model = transformers.AutoModelForCausalLM.from_pretrained(model_name_or_path, load_in_8bit=True, device_map='auto', torch_dtype=torch.float16)
    
    # if training_args.local_rank == 0:
    #     print('='*100)
    #     print(training_args)
    
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

    # if training_args.local_rank == 0:
    print("Load model from {} over.".format(args.model_name_or_path))


    # raw_train_datasets = load_dataset(
    #     'json',
    #     data_files=data_args.data_path,
    #     split="train",
    #     cache_dir=training_args.cache_dir
    # )

    if args.task == 'train':
        raw_train_datasets = load_dataset(
            args.data_path,
            split="train",
        )
    else:
        raw_train_datasets = load_dataset(
            args.data_path,
            split="train[:5%]",
        )

    # if training_args.local_rank > 0: 
    #     torch.distributed.barrier()

    if 'deepseek' in args.model_name_or_path:  
        train_dataset = raw_train_datasets.map(
            deepseek_train_tokenize_function,
            batched=True,
            batch_size=3000,
            num_proc=32,
            remove_columns=raw_train_datasets.column_names,
            load_from_cache_file=True, # not args.overwrite_cache
            desc="Running Encoding",
            fn_kwargs={ "tokenizer": tokenizer , "task": args.task}
        )
    else:
        train_dataset = raw_train_datasets.map(
            codellama_train_tokenize_function,
            batched=True,
            batch_size=3000,
            num_proc=32,
            remove_columns=raw_train_datasets.column_names,
            load_from_cache_file=True, # not args.overwrite_cache
            desc="Running Encoding",
            fn_kwargs={ "tokenizer": tokenizer }
        )

    # if training_args.local_rank == 0:
    #     torch.distributed.barrier()
    
    # if training_args.local_rank == 0:
    #     print("Training dataset samples:", len(train_dataset))
    #     for index in random.sample(range(len(train_dataset)), 3):
    #         print(f"Sample {index} of the training set: {train_dataset[index]['input_ids']}, {train_dataset[index]['labels']}.")
    #         print(f"Sample {index} of the training set: {tokenizer.decode(list(train_dataset[index]['input_ids']))}.")

    data_collator = DataCollatorForSupervisedDataset(tokenizer=tokenizer)
    # data_module = dict(train_dataset=train_dataset, eval_dataset=None, data_collator=data_collator)

    # trainer = Trainer(model=model, tokenizer=tokenizer, args=training_args, **data_module)

    # trainer.train()
    # trainer.save_state()
    # safe_save_model_for_hf_trainer(trainer=trainer, output_dir=training_args.output_dir)

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
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
        eval_dataset=None,
    )

    # Start training
    if args.task == 'train': 
        trainer.train()

    model.save_pretrained(training_args.output_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=str, default='finetune')
    parser.add_argument("--batch_size", default=1, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_name_or_path", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--data_path", type=str, default='zhaospei/refine-v2')
    parser.add_argument("--output_file", type=str, default="gen.output")
    parser.add_argument("--output_dir", type=str, default='tmp/scg-13-01-24')
    parser.add_argument("--model_max_length", type=int, default=2048)
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()
    train(args)

if __name__ == "__main__":
    main()