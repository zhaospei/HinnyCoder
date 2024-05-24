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
    output = ' '.join(output.split()[:30])
    return output

def deepseek_build_masked_func(masked_func: str):
    """
    Mask the function body with special tokens.
    """
    masked_func = masked_func.replace('FILL_FUNC_BODY', FILL_TOKEN)
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
    # print(tokenizer)
    sources = [
        deepseek_build_masked_func(masked_class_with_comment)
        for masked_class_with_comment in dataset['masked_class_with_comment']
    ]

    # batch_list = split_batch(sources, args.batch_size)
    # len_batch = len(sources) // args.batch_size
    with tqdm(total=len(sources), desc="gen") as pbar:
        for prompt in sources:
            model_inputs = tokenizer(
                prompt,
                return_tensors="pt",
                max_length=args.max_length,
                truncation=True
            )
            model_inputs = {k: v.to("cuda") for k, v in model_inputs.items()}
            
            # with torch.no_grad():
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=True,
                num_return_sequences=args.num_return_sequences,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=32021
            )
            
            # truncated_ids = [ids[len(model_inputs[idx]):] for idx, ids in enumerate(generated_ids)]
            truncated_ids = [ids[len(model_inputs[0]):] for ids in generated_ids]
            generated_texts = [tokenizer.decode(output, skip_special_tokens=True) for output in truncated_ids]
            
            for text in generated_texts:
                try:
                    write_string_to_file(args.output_file, text + '<candidate>')
                except Exception as e:
                    print(e)
                    write_string_to_file(args.output_file, '<candidate>')
            # try:
            write_string_to_file(args.output_file, '<nl>')
            # except Exception as e:
            #     print(e)
            #     write_string_to_file(args.output_file, '<candidate>')
            # print(generated_texts)
        # for prompt in sources:
        #     model_inputs = tokenizer(
        #         prompt,
        #         return_tensors="pt",
        #         max_length=args.max_length,
        #         truncation=True
        #     )
        #     model_inputs = {k: v.to("cuda") for k, v in model_inputs.items()}
            
        #     # with torch.no_grad():
        #     generated_ids = model.generate(
        #         **model_inputs,
        #         max_new_tokens=args.max_new_tokens,
        #         do_sample=True,
        #         num_return_sequences=args.num_return_sequences,
        #         pad_token_id=tokenizer.pad_token_id,
        #         eos_token_id=32021
        #     )
            
        #     generated_texts = [tokenizer.decode(output, skip_special_tokens=True) for output in generated_ids]
        #     print(generated_texts)

        # for prompt in sources:
        #     model_inputs = tokenizer(
        #         prompt,
        #         return_tensors="pt",
        #         padding=True,
        #         max_length=args.max_length,
        #         truncation=True
        #     )
            
        #     model_inputs = {k: v.to("cuda") for k, v in model_inputs.items()}
        #         # for key, value in model_inputs.items():
        #         #     print(f"{key}: {value.shape}, dtype: {value.dtype}, device: {value.device}")
        #     generated_ids = model.generate(
        #         **model_inputs,
        #         max_new_tokens=args.max_new_tokens,
        #         do_sample=True,
        #         num_return_sequences=args.num_return_sequences,
        #         pad_token_id=tokenizer.pad_token_id,
        #         eos_token_id=32021
        #     )
            

        #     generated_texts = [tokenizer.decode(output, skip_special_tokens=True) for output in generated_ids]
        #     print(generated_texts)

            pbar.update(1)

def main():
    """
    Main function to run the inference script.
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument("--batch_size", default=1, type=int,
    #                     help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_peft", type=str, default='')
    parser.add_argument("--top_k", type=str, default='50')
    parser.add_argument("--num_return_sequences", type=int, default='2')
    # parser.add_argument("--do_sample", action='store_true')
    parser.add_argument("--model_id", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--dataset_id", type=str, default='zhaospei/python-gold')
    parser.add_argument("--output_file", type=str, default="gen.output")
    parser.add_argument("--max_length", type=int, default=400)
    parser.add_argument("--padding", type=str, default='longest')
    parser.add_argument("--max_new_tokens", type=int, default=30)
    parser.add_argument("--data_split", type=str, default='test')
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
