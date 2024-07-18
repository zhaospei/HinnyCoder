import torch
import argparse
from tqdm import tqdm
from peft import PeftModel
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM

def split_batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'a') as fout:
        fout.write(string)

def build_relevant_context(str):
    if str.strip() != '':
        return "\n// Here are some relevant code fragments from other files of the repo:\n" + str
    else:
        return str        

def main(args):

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    if args.load_in_8bit:
        model = AutoModelForCausalLM.from_pretrained(args.model_path, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map='auto', load_in_8bit=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model_path, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map='auto').cuda()
    
    # model = PeftModel.from_pretrained(model, args.model_peft)
    # print('Loaded peft model from ', args.model_peft)

    print("\n====== Start inferencing ======\n")
    model.eval()
    
    tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "left"

    dataset = load_dataset(args.dataset_path, split='test')
    
    list_context = []
    
    if len(args.cols) == 0:
        print("Please specify the columns to be used for inferencing")
    
    for col in args.cols:
        list_context.append(dataset[col])
    
    context = ['\n'.join(x) for x in zip(*list_context)]
    
    sources = [
        '<｜fim▁begin｜>' + masked_class.replace('<FILL_FUNCTION_BODY>', '<｜fim▁hole｜>') + build_relevant_context(context) + '<｜fim▁end｜>'
        for (masked_class, context ) in zip(
            dataset['masked_class'],
            context,
        )
    ]
    
    
    print("\n====== Start testing max input ======\n")
    max_len_input_str = max(sources, key=len)
    model_inputs = tokenizer(max_len_input_str, return_tensors="pt", padding=True, max_length=args.max_len_input, truncation=True).to("cuda")
    generated_ids = model.generate(**model_inputs, max_new_tokens=args.max_len_output, pad_token_id=tokenizer.eos_token_id)
    print("\n====== Pass ======\n")
    batch_list = split_batch(sources, args.batch_size)
    len_batch = len(sources) // args.batch_size
    with tqdm(total=len_batch, desc="gen") as pbar:
        for batch in batch_list:
            model_inputs = tokenizer(batch, return_tensors="pt", padding=True, max_length=args.max_len_input, truncation=True).to("cuda")
            generated_ids = model.generate(**model_inputs, max_new_tokens=args.max_len_output, pad_token_id=tokenizer.eos_token_id)

            truncated_ids = [ids[len(model_inputs[idx]):] for idx, ids in enumerate(generated_ids)]

            output = tokenizer.batch_decode(truncated_ids, skip_special_tokens=True)

            for idx, source in enumerate(batch):
                try:
                    out = output[idx]
                    write_string_to_file(args.output_file, out + '<nl>')
                except Exception as e:
                    print(e)
                    write_string_to_file(args.output_file, '<nl>')
            pbar.update(1)

    print("\n====== Finish inferencing ======\n")
    
    print("Output file is saved at ", args.output_file)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cols", default='[]', nargs='+', type=str,
                        help="Task to perform: e.g. baseline, peft")
    parser.add_argument("--dataset_path", default='zhaospei/500_parent_param_context', type=str,
                        help="Path to dataset for inferencing")
    parser.add_argument("--model_path", default="deepseek-ai/deepseek-coder-6.7b-base", type=str,
                        help="Path to pre-trained model: e.g. roberta-base, codellama/CodeLlama-7b-hf, Salesforce/codet5-base")
    parser.add_argument("--batch_size", default=1, type=int,
                        help="Batch size per GPU/CPU for training.")
    parser.add_argument("--load_in_8bit", action='store_true',
                        help="Load model 8 bit.")
    parser.add_argument("--model_peft", type=str, default='output/')
    parser.add_argument("--max_len_input", default=10000, type=int,
                        help="The maximum total source sequence length after tokenization")
    parser.add_argument("--max_len_output", default=400, type=int,
                        help="The maximum total target sequence length after tokenization")
    parser.add_argument("--output_file", type=str, default="gen.output")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    main(args)
