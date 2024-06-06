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

def deepseek_build_output_compiler(output: str):
    """
    Mask the function body with special tokens.
    """
    output = output.replace('<COMPILED_SUCCESSFULLY>', 'success')
    # output = ' '.join(output.split()[:30])
    return output

def deepseek_build_masked_func(masked_func: str):
    """
    Mask the function body with special tokens.
    """
    masked_func = masked_func.replace('FILL_FUNC_BODY', FILL_TOKEN + '\n')
    return BEGIN_TOKEN + masked_func + END_TOKEN

def gemma_build_masked_func(masked_func):
    """
    Mask the function body with special tokens.
    """
    # masked_func = masked_func.replace('FILL_FUNC_BODY', '<FILL_ME>')
    # return masked_func
    prefix_tokens, suffix_tokens = masked_func.split('FILL_FUNC_BODY')
    return '<|fim_prefix|>' + prefix_tokens + '<|fim_suffix|>' + suffix_tokens + '<|fim_middle|>'

def starcoder_build_masked_func(masked_func):
    """
    Mask the function body with special tokens.
    """
    # masked_func = masked_func.replace('FILL_FUNC_BODY', '<FILL_ME>')
    # return masked_func
    prefix_tokens, suffix_tokens = masked_func.split('FILL_FUNC_BODY')
    return '<fim_prefix>' + prefix_tokens + '<fim_suffix>' + suffix_tokens + '<fim_middle>'

def codellama_build_masked_func(masked_func):
    """
    Mask the function body with special tokens.
    """
    # masked_func = masked_func.replace('FILL_FUNC_BODY', '<FILL_ME>')
    # return masked_func
    prefix_tokens, suffix_tokens = masked_func.split('FILL_FUNC_BODY')
    return '▁<PRE>' + prefix_tokens + '▁<SUF>' + suffix_tokens + '▁<MID>'

def split_batch(iterable, n=1):
    """
    Split a list into batches of size n.
    """
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def write_string_to_file(absolute_filename, string):
    """
    Write a string to a file.
    """
    with open(absolute_filename, 'a') as fout:
        fout.write(string)

def run(args):
    """
    Run the inference script.
    """
    dataset_id = args.dataset_id
    model_id = args.model_id

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
    if args.load_in_8bit:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            device_map='auto',
            load_in_8bit=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            device_map='auto'
        ).cuda()

    if args.model_peft != '':
        print('Loading peft model from ', args.model_peft)
        model = PeftModel.from_pretrained(model, args.model_peft)

    model.eval()

    if 'codellama' in args.model_id or 'star' in args.model_id:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "left" # Fix weird overflow issue with fp16 training

    dataset = datasets.load_dataset(dataset_id, split=args.data_split)
    print(tokenizer)
    if args.task == 'gen_baseline':
        if 'deepseek' in args.model_id:
            sources = [
                deepseek_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        elif 'llama' in args.model_id:
            sources = [
                codellama_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        elif 'gemma' in args.model_id:
            sources = [
                gemma_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        elif 'star' in args.model_id:
            sources = [
                starcoder_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        else:
            print('Model not supported')
            sys.exit(1)
    elif args.task == 'gen_finetune':
        if 'deepseek' in args.model_id:
            sources = [
                deepseek_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        elif 'llama' in args.model_id:
            sources = [
                codellama_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        elif 'gemma' in args.model_id:
            sources = [
                gemma_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        elif 'star' in args.model_id:
            sources = [
                starcoder_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
        else:
            print('Model not supported')
            sys.exit(1)
    elif args.task == 'gen_final':
        sources = [
            deepseek_build_masked_func(instruction)
            + '\n<ouput>\n' + output
            + '\n<compile>\n' + deepseek_build_output_compiler(compile_info)
            + '\n<inherit>\n' + inherit_elements
            +'\n<correct> '
            for (instruction, output, compile_info, inherit_elements) in zip(
                dataset['masked_class_with_comment'],
                dataset['finetune_output'],
                dataset['pylint_output'],
                dataset['relevant_context']
            )
        ]
    elif args.task == 'gen_refine':
        sources = [
            deepseek_build_masked_func(instruction)
            + '\n<ouput>\n' + output
            + '\n<pylint>\n' + deepseek_build_output_compiler(compile_info)
            + '\n<correct> '
            for (instruction, output, compile_info) in zip(
                dataset['masked_class_with_comment'],
                dataset['finetune_output'],
                dataset['pylint_output']
            )
        ]
    elif args.task == "gen_disable":
         sources = [
                deepseek_build_masked_func(instruction)
                + '\n<ouput>\n' + output
                + '\n<inherit>\n' + inherit_elements +
                '\n<correct> '
                for (instruction, output, inherit_elements) in zip(
                    dataset['masked_class_with_comment'],
                    dataset['finetune_output'],
                    dataset['relevant_context']
                )
            ]
    else:
        print('Task not supported')
        sys.exit(1)

    batch_list = split_batch(sources, args.batch_size)
    len_batch = len(sources) // args.batch_size
    with tqdm(total=len_batch, desc="gen") as pbar:
        for batch in batch_list:
            if args.padding == 'longest':
                model_inputs = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    max_length=args.max_length,
                    truncation=True
                ).to("cuda")
            else:
                model_inputs = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding='max_length',
                    max_length=args.max_length,
                    truncation=True
                ).to("cuda")
                # model_inputs = tokenizer(batch, return_tensors="pt", padding=True).to("cuda")
            
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )

            truncated_ids = [ids[len(model_inputs[idx]):] for idx, ids in enumerate(generated_ids)]

            output = tokenizer.batch_decode(
                truncated_ids,
                skip_special_tokens=True
            )

            for idx, _ in enumerate(batch):
                try:
                    write_string_to_file(args.output_file, output[idx] + '<nl>')
                except Exception as e:
                    print(e)
                    write_string_to_file(args.output_file, '<nl>')

            pbar.update(1)
def main():
    """
    Main function to run the inference script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default='gen_baseline', type=str)
    parser.add_argument("--batch_size", default=1, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_peft", type=str, default='')
    parser.add_argument("--model_id", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--dataset_id", type=str, default='zhaospei/python-gold')
    parser.add_argument("--output_file", type=str, default="gen.output")
    parser.add_argument("--max_length", type=int, default=2100)
    parser.add_argument("--padding", type=str, default='longest')
    parser.add_argument("--max_new_tokens", type=int, default=400)
    parser.add_argument("--data_split", type=str, default='test')
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
