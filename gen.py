import torch
from transformers import AutoModelForCausalLM, CodeLlamaTokenizer
from tqdm import tqdm
from peft import PeftModel
import json

def read_contextual_medit_examples(filename):
    """Read examples from filename."""
    examples = []
    with open(filename, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            js = json.loads(line)
            examples.append(js['prompt'])
    return examples

def write_string_to_file(absolute_filename, string):
        with open(absolute_filename, 'a') as fout:
            fout.write(string)

def gen(model_base, model_peft, input_file, output_file):
    tokenizer = CodeLlamaTokenizer.from_pretrained(model_base)

    model = AutoModelForCausalLM.from_pretrained(model_base, load_in_8bit=True, device_map='auto', torch_dtype=torch.float16)

    model = PeftModel.from_pretrained(model, model_peft)

    model.eval()

    examples = read_contextual_medit_examples(input_file)

    for eval_prompt in tqdm(examples):
        model_input = tokenizer(eval_prompt, return_tensors="pt").to("cuda")

        output = ''

        with torch.no_grad():
            output = tokenizer.decode(model.generate(**model_input, max_new_tokens=32, pad_token_id=tokenizer.eos_token_id)[0], skip_special_tokens=True)
        write_string_to_file(output_file, '' + output + '<nl>')

if __name__ == "__main__":
    gen('codellama/CodeLlama-7b-hf', '/home/dungbt/llama/tmp/code-llama-output', 'test.input.jsonl', 'test.codellama.reload.output')