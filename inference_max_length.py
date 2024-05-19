from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import datasets
import argparse
from tqdm import tqdm
# import logging
# logging.disable(logging.WARNING)

from peft import PeftModel

BEGIN_TOKEN = "<｜fim▁begin｜>"
FILL_TOKEN = "<｜fim▁hole｜>"
END_TOKEN = "<｜fim▁end｜>"
IGNORE_INDEX = -100
EOT_TOKEN = "<|EOT|>"

def deepseek_build_output_compiler(output: str):
    output = output.replace('<COMPILED_SUCCESSFULLY>', 'success')
    output = ' '.join(output.split()[:30])
    return output

def deepseek_build_masked_func(masked_func: str):
    masked_func = masked_func.replace('FILL_FUNC_BODY', FILL_TOKEN)
    return BEGIN_TOKEN + masked_func + END_TOKEN

def gemma_build_masked_func(masked_func):
    # masked_func = masked_func.replace('FILL_FUNC_BODY', '<FILL_ME>')
    # return masked_func
    prefix_tokens, suffix_tokens = masked_func.split('FILL_FUNC_BODY')
    return '<|fim_prefix|>' + prefix_tokens + '<|fim_suffix|>' + suffix_tokens + '<|fim_middle|>'

def starcoder_build_masked_func(masked_func):
    # masked_func = masked_func.replace('FILL_FUNC_BODY', '<FILL_ME>')
    # return masked_func
    prefix_tokens, suffix_tokens = masked_func.split('FILL_FUNC_BODY')
    return '<fim_prefix>' + prefix_tokens + '<fim_suffix>' + suffix_tokens + '<fim_middle>'

def codellama_build_masked_func(masked_func):
    # masked_func = masked_func.replace('FILL_FUNC_BODY', '<FILL_ME>')
    # return masked_func
    prefix_tokens, suffix_tokens = masked_func.split('FILL_FUNC_BODY')
    return '▁<PRE>' + prefix_tokens + '▁<SUF>' + suffix_tokens + '▁<MID>'

def split_batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'a') as fout:
        fout.write(string)

def run(args):
    dataset_id = args.dataset_id
    model_id = args.model_id

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, )
    # print(tokenizer)
    if args.load_in_8bit:
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map='auto', load_in_8bit=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map='auto').cuda()
    if args.model_peft != '':
        print('Loading peft model from ', args.model_peft)
        model = PeftModel.from_pretrained(model, args.model_peft)

    model.eval()
    if 'codellama' in args.model_id or 'star' in args.model_id:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "left" # Fix weird overflow issue with fp16 training

    dataset = datasets.load_dataset(dataset_id, split=args.data_split)
    # dataset = datasets.load_dataset(dataset_id, split="train[:1]")

    # train_dataset = raw_train_datasets.map(
    #     train_tokenize_function,
    #     batched=True,
    #     batch_size=3000,
    #     num_proc=32,
    #     remove_columns=raw_train_datasets.column_names
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
        else:
            sources = [
                starcoder_build_masked_func(masked_class_with_comment)
                for masked_class_with_comment in dataset['masked_class_with_comment']
            ]
            # print(sources)
    elif args.task == 'gen_final':
        sources = [
            deepseek_build_masked_func(instruction) + '\n<ouput>\n' + output + '\n<compile>\n' + deepseek_build_output_compiler(compile_info) + '\n<inherit>\n' + inherit_elements + '\n<correct> '
            for (instruction, output, compile_info, inherit_elements) in zip(dataset['masked_class_with_comment'], dataset['deepseek_output'], dataset['compile_info'], dataset['inherit_elements'])
        ]
    elif args.task == 'gen_disable':
        sources = [
            deepseek_build_masked_func(instruction) + '\n<ouput>\n' + output + '\n<inherit>\n' + inherit_elements + '\n<correct> '
            for (instruction, output, compile_info, inherit_elements) in zip(dataset['masked_class_with_comment'], dataset['deepseek_output'], dataset['compile_info'], dataset['inherit_elements'])
        ]
    else:
        if 'deepseek' in args.model_id:
            sources = [
                deepseek_build_masked_func(instruction) + '\n<ouput>\n' + output + '\n<compile>\n' + deepseek_build_output_compiler(compile_info) + '\n<correct> '
                for (instruction, output, compile_info) in zip(dataset['masked_class_with_comment'], dataset['deepseek_output'], dataset['compile_info'])
            ]
        else:
            sources = [
                deepseek_build_masked_func(instruction) + '\n<ouput>\n' + output + '\n<compile>\n' + deepseek_build_output_compiler(compile_info) + '\n<correct> '
                for (instruction, output, compile_info) in zip(dataset['masked_class_with_comment'], dataset['deepseek_output'], dataset['compile_info'])
            ]

    batch_list = split_batch(sources, args.batch_size)
    len_batch = len(sources) // args.batch_size
    with tqdm(total=len_batch, desc="gen") as pbar:
        for batch in batch_list:
            if args.padding == 'longest':
                model_inputs = tokenizer(batch, return_tensors="pt", padding=True, max_length=args.max_length, truncation=True).to("cuda")
            else:
                model_inputs = tokenizer(batch, return_tensors="pt", padding='max_length', max_length=args.max_length, truncation=True).to("cuda")
                # model_inputs = tokenizer(batch, return_tensors="pt", padding=True).to("cuda")
            

            if args.task == 'gen_baseline':
                generated_ids = model.generate(**model_inputs, max_length=args.max_length, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
            else:
                if 'deepseek' in args.model_id:
                    generated_ids = model.generate(**model_inputs, max_length=args.max_length, pad_token_id=tokenizer.pad_token_id, eos_token_id=32021)
                else:
                    generated_ids = model.generate(**model_inputs, max_length=args.max_length, pad_token_id=tokenizer.eos_token_id)
            
            # print(tokenizer.decode(generated_ids[0], skip_special_tokens=True))

            truncated_ids = [ids[len(model_inputs[idx]):] for idx, ids in enumerate(generated_ids)]

            output = tokenizer.batch_decode(truncated_ids, skip_special_tokens=True)

            for idx, source in enumerate(batch):
                # print(idx, source)
                # write_string_to_file(args.output_file, output[idx][len(source):] + '<nl>')
                # output[idx] = output[idx].encode('utf-8')
                try:
                    write_string_to_file(args.output_file, output[idx] + '<nl>')
                except Exception as e:
                    print(e)
                    write_string_to_file(args.output_file, '<nl>')
                # print(output[0][len(sources[0]):], output[1][len(sources[1]):])
            pbar.update(1)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default='gen_baseline', type=str)
    parser.add_argument("--batch_size", default=2, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_peft", type=str, default='')
    parser.add_argument("--model_id", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--dataset_id", type=str, default='zhaospei/2048_pylint_no_init')
    parser.add_argument("--output_file", type=str, default="gen.output")
    parser.add_argument("--max_length", type=int, default=2048)
    parser.add_argument("--padding", type=str, default='longest')
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument("--data_split", type=str, default='test')
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
