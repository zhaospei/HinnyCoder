import copy
import datasets

def get_preprocessed_scg(dataset_id, tokenizer, split):
    dataset = datasets.load_dataset(dataset_id, split=split)

    def tokenize_add_label(sample):
        prompt = tokenizer.encode(tokenizer.bos_token + sample["prompt"], add_special_tokens=False, max_length=31, truncation=True)
        func_code = tokenizer.encode(sample["func_code"] +  tokenizer.eos_token, max_length=301, truncation=True, add_special_tokens=False)
        max_length = 333 - len(prompt) - len(func_code)
        # mx = max(mx, len(prompt) + len(message))
        if max_length < 0:
            print("OK")

        pad = tokenizer.encode(tokenizer.eos_token, add_special_tokens=False, max_length=max_length, padding='max_length', truncation=True)

        sample = {
            "input_ids": prompt + func_code + pad,
            "attention_mask" : [1] * (len(prompt) + len(func_code) + len(pad)),
            "labels": [-100] * len(prompt) + func_code + [-100] * len(pad),
            }

        return sample
    
    dataset = dataset.map(tokenize_add_label, remove_columns=list(dataset.features))
    return dataset