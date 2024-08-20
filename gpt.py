import concurrent.futures
import copy
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

CWD = os.path.abspath(os.path.dirname(__file__))
load_dotenv(override=True)

# Setting API parameters
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def extract_code_block(completion_string: str, language: str = "java") -> str:
    """Get the code block from the LLM answer

    Args:
        completion_string (str): LLM answer

    Returns:
        str: Code block
    """
    if f"```{language}" in completion_string:
        completion_string = completion_string[
            completion_string.find(f"```{language}") + len(f"```{language}") :
        ]
        completion_string = completion_string[: completion_string.find("```")]
    else:
        print("Error: No code block found")
    return completion_string


def fetch_completion(
    data_entry: dict, model: str = "", language: str = "java"
) -> dict:
    prompt = (
        "**Role**: You are a software programmer.\n"
        "**Task**: As a programmer, you are required to fill the function body which is now marking by <infilling> token\n"
        "**Code Formatting**: Please write only infilling code in\n"
        "```java\n"
        "[Code]\n"
        "```\n"
        "format.\n"
        "{}".format(data_entry["prompt"])
    )
    while True:
        try:
            completions = client.chat.completions.create(
                model=model,
                stream=False,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a software programmer.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.0,
            )
            completion = completions.choices[0].message.content
            code_block = extract_code_block(completion)
        except Exception as e:
            print(repr(e))
            time.sleep(10)
            code_block = ""
        if code_block != "":
            break
    # print(code_block)
    data_entry["prediction"] = code_block
    return data_entry


if __name__ == "__main__":
    model = "gpt-3.5-turbo"
    language = "java"
    df = pd.read_json(
        f"{CWD}/data/rambo_baseline.jsonl", lines=True, orient="records"
    )
    dataset = df.to_dict(orient="records")
    dataset = dataset[20:]
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_entry = {
            executor.submit(
                fetch_completion, copy.deepcopy(entry), model, language
            ): entry
            for entry in dataset
        }
        for future in tqdm(
            concurrent.futures.as_completed(future_to_entry),
            total=len(future_to_entry),
            desc="Generating code",
        ):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))
    print("Generate code first time done!")
    updated_df = pd.DataFrame(dataset)
    updated_df.to_json(
        f"{CWD}/data/rambo_baseline_res1.jsonl",
        lines=True,
        orient="records",
    )
