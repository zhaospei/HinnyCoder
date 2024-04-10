from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer
import argparse


def train(args):
    model_path = args.model_name_or_path
    quant_path = args.hub_model_path
    quant_config = { "zero_point": True, "q_group_size": 128, "w_bit": 4, "version": "GEMM" }

    # Load model
    model = AutoAWQForCausalLM.from_pretrained(model_path, **{"low_cpu_mem_usage": True})
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    # Quantize
    model.quantize(tokenizer, quant_config=quant_config)

    # Save quantized model
    model.save_quantized(quant_path)
    tokenizer.save_pretrained(quant_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name_or_path", type=str, default='deepseek-ai/deepseek-coder-6.7b-base')
    parser.add_argument("--hub_model_path", type=str, default='')
    args = parser.parse_args()
    train(args)

if __name__ == "__main__":
    main()