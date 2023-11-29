import copy
import datasets

def get_preprocessed_type(dataset_id, tokenizer, split):
    dataset = datasets.load_dataset(dataset_id, split=split)

    prompt = (
        f"Give a short commit message for code from git diff with type_{{type}}:\n{{diff}}\n---\nShort commit message:\n"
    )

    def apply_prompt_template(sample):
        return {
            "prompt": prompt.format(type=sample["type"], diff=sample["diff"]),
            "message": sample["msg"],
        }

    dataset = dataset.map(apply_prompt_template, remove_columns=list(dataset.features))

    # mx = 0

    def tokenize_add_label(sample):
        prompt = tokenizer.encode(tokenizer.bos_token + sample["prompt"], add_special_tokens=False, max_length=991, truncation=True)
        message = tokenizer.encode(sample["message"] +  tokenizer.eos_token, max_length=32, truncation=True, add_special_tokens=False)
        max_length = 1024 - len(prompt) - len(message)
        # mx = max(mx, len(prompt) + len(message))
        if max_length < 0:
            print("OK")

        pad = tokenizer.encode(tokenizer.eos_token, add_special_tokens=False, max_length=max_length, padding='max_length', truncation=True)

        sample = {
            "input_ids": prompt + message + pad,
            "attention_mask" : [1] * (len(prompt) + len(message) + len(pad)),
            "labels": [-100] * len(prompt) + message + [-100] * len(pad),
            }

        return sample
    
    dataset = dataset.map(tokenize_add_label, remove_columns=list(dataset.features))

    # print(mx)
    return dataset

def get_preprocessed_cmg(dataset_id, tokenizer, split):
    dataset = datasets.load_dataset(dataset_id, split=split)

    prompt = (
        f"Give a short commit message for code from git diff:\n{{diff}}\n---\nShort commit message:\n"
    )

    def apply_prompt_template(sample):
        return {
            "prompt": prompt.format(diff=sample["diff"]),
            "message": sample["msg"],
        }

    dataset = dataset.map(apply_prompt_template, remove_columns=list(dataset.features))

    # mx = 0

    def tokenize_add_label(sample):
        prompt = tokenizer.encode(tokenizer.bos_token + sample["prompt"], add_special_tokens=False, max_length=991, truncation=True)
        message = tokenizer.encode(sample["message"] +  tokenizer.eos_token, max_length=32, truncation=True, add_special_tokens=False)
        max_length = 1024 - len(prompt) - len(message)
        # mx = max(mx, len(prompt) + len(message))
        if max_length < 0:
            print("OK")

        pad = tokenizer.encode(tokenizer.eos_token, add_special_tokens=False, max_length=max_length, padding='max_length', truncation=True)

        sample = {
            "input_ids": prompt + message + pad,
            "attention_mask" : [1] * (len(prompt) + len(message) + len(pad)),
            "labels": [-100] * len(prompt) + message + [-100] * len(pad),
            }

        return sample
    
    dataset = dataset.map(tokenize_add_label, remove_columns=list(dataset.features))

    # print(mx)
    return dataset

def get_preprocessed_cmg_history(dataset_id, tokenizer, split):
    dataset = datasets.load_dataset(dataset_id, split=split)

    prompt = (
        f"Give a short commit message for code from:\n- History commit messages:\n{{vccs}}\n- Git diff:\n{{diff}}\n---\nShort commit message:\n"
    )

    def apply_prompt_template(sample):
        return {
            "prompt": prompt.format(vccs=sample['vccs_msg'], diff=sample["diff"]),
            "message": sample["msg"],
        }

    dataset = dataset.map(apply_prompt_template, remove_columns=list(dataset.features))

    # mx = 0

    def tokenize_add_label(sample):
        prompt = tokenizer.encode(tokenizer.bos_token + sample["prompt"], add_special_tokens=False, max_length=991, truncation=True)
        message = tokenizer.encode(sample["message"] +  tokenizer.eos_token, max_length=32, truncation=True, add_special_tokens=False)
        max_length = 1024 - len(prompt) - len(message)
        # mx = max(mx, len(prompt) + len(message))
        if max_length < 0:
            print("OK")

        pad = tokenizer.encode(tokenizer.eos_token, add_special_tokens=False, max_length=max_length, padding='max_length', truncation=True)

        sample = {
            "input_ids": prompt + message + pad,
            "attention_mask" : [1] * (len(prompt) + len(message) + len(pad)),
            "labels": [-100] * len(prompt) + message + [-100] * len(pad),
            }

        return sample
    
    dataset = dataset.map(tokenize_add_label, remove_columns=list(dataset.features))

    # print(mx)
    return dataset

def get_preprocessed_type_history(dataset_id, tokenizer, split):
    dataset = datasets.load_dataset(dataset_id, split=split)

    prompt = (
        f"Give a short commit message for code with type_{{type}} from:\n- History commit messages:\n{{vccs}}\n- Git diff:\n{{diff}}\n---\nShort commit message:\n"
    )

    def apply_prompt_template(sample):
        return {
            "prompt": prompt.format(type=sample['type'], vccs=sample['vccs_msg'], diff=sample["diff"]),
            "message": sample["msg"],
        }

    dataset = dataset.map(apply_prompt_template, remove_columns=list(dataset.features))

    # mx = 0

    def tokenize_add_label(sample):
        prompt = tokenizer.encode(tokenizer.bos_token + sample["prompt"], add_special_tokens=False, max_length=991, truncation=True)
        message = tokenizer.encode(sample["message"] +  tokenizer.eos_token, max_length=32, truncation=True, add_special_tokens=False)
        max_length = 1024 - len(prompt) - len(message)
        # mx = max(mx, len(prompt) + len(message))
        if max_length < 0:
            print("OK")

        pad = tokenizer.encode(tokenizer.eos_token, add_special_tokens=False, max_length=max_length, padding='max_length', truncation=True)

        sample = {
            "input_ids": prompt + message + pad,
            "attention_mask" : [1] * (len(prompt) + len(message) + len(pad)),
            "labels": [-100] * len(prompt) + message + [-100] * len(pad),
            }

        return sample
    
    dataset = dataset.map(tokenize_add_label, remove_columns=list(dataset.features))

    # print(mx)
    return dataset