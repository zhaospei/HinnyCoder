import argparse
import pandas as pd
from typing import List, Optional

def calc_em(prediction: List[str], ground_truth: List[str]) -> str:
    assert len(prediction) == len(ground_truth), "Number of prediction and ground truth must be the same"
    cnt = 0
    for pred, gt in zip(prediction, ground_truth):
        normalize_pred = ' '.join(pred.split())
        normalize_gt = ' '.join(gt.split())
        if normalize_gt == normalize_pred:
            cnt += 1
    return "{:.2f}".format(cnt * 100 / len(prediction))


def find_comment(source: str) -> Optional[List[dict]]:
    """This function aims to find all comments in Solidity source code

    Args:
        source (str): Solidity source code

    Returns:
        List[dict]: List of dictionary contains comment's information
    """
    source = source.replace("\r\n", "\n")
    state = "ETC"
    i = 0
    comments = []
    currentComment = None

    while i + 1 < len(source):
        if state == "ETC" and source[i] == "/" and source[i + 1] == "/":
            state = "LINE_COMMENT"
            currentComment = {"type": "LineComment", "range": {"start": i}}
            i += 2
            continue

        if state == "LINE_COMMENT" and source[i] == "\n":
            state = "ETC"
            currentComment["range"]["end"] = i
            comments.append(currentComment)
            currentComment = None
            i += 1
            continue

        if state == "ETC" and source[i] == "/" and source[i + 1] == "*":
            state = "BLOCK_COMMENT"
            currentComment = {"type": "BlockComment", "range": {"start": i}}
            i += 2
            continue

        if state == "BLOCK_COMMENT" and source[i] == "*" and source[i + 1] == "/":
            state = "ETC"
            currentComment["range"]["end"] = i + 2
            comments.append(currentComment)
            currentComment = None
            i += 2
            continue
        i += 1

    if currentComment and currentComment["type"] == "LineComment":
        if source[i - 1] == "\n":
            currentComment["range"]["end"] = len(source) - 1
        else:
            currentComment["range"]["end"] = len(source)

        comments.append(currentComment)

    return comments


def remove_comment(source: str) -> str:
    """This function aims to remove all comments in Solidity source code

    Args:
        source (str): Original Solidity source code

    Returns:
        str: Source code after remove comments
    """
    source = source.replace("\r\n", "\n")
    comments = find_comment(source)
    removed_comment = ""
    begin = 0
    for comment in comments:
        removed_comment += source[begin : comment["range"]["start"]]
        begin = comment["range"]["end"]
    removed_comment += source[begin:]
    return removed_comment


def calc_em_removed_comment(prediction: List[str], ground_truth: List[str]) -> str:
    removed_comment_prediction = list(map(lambda code: remove_comment(code), prediction))
    remove_comment_ground_truth = list(map(lambda code: remove_comment(code), ground_truth))
    return calc_em(removed_comment_prediction, remove_comment_ground_truth)


def main(args):
    df = pd.read_json(args.input, lines=True)
    flaw = [
        "5e41187c16e6acd79f435b1a18312ee7ed86ff3a228e95c6269e523e78c37552",
        "c65e93ae3eb54f0f0812e0231fd992503a7b113314a5e62492d6cf555487fe24",
        "cc7b53b6a234d2b7f952bc7cf38c6206f4a7910491d8a0c414ed4600f17588c1",

        "37497bed336eb012890fc7770295b46f192ccf65b0f828d783eedd1a47cdafb5",
        "cc8f907557109ee35b048274c78d08e61cfb8579560cb8b9aef4fd0503453e42",
        "cca1fe2017686735e48e23576404d10dde66cfc5926280308f0f99fab1377f0c",
        "fae7ab2c7d32932ef3e7c0aea28f376b843bb53fe6dbcd8bf8f2f8ac2657c051"
        ]
    df.drop(index=df[df["task_id"].isin(flaw)].index, inplace=True)
    assert "prediction" in df.columns, "No prediction column"
    assert "ground_truth" in df.columns or "func_body" in df.columns, "No ground truth column"
    prediction = df["prediction"].tolist()
    if "ground_truth" in df.columns:
        ground_truth = df["ground_truth"].tolist()
    else:
        ground_truth = df["func_body"].tolist()
    print("EM".ljust(20, ' '), ':', calc_em(prediction, ground_truth))
    # print("CodeBLEU".ljust(20, ':', calc_codebleu(prediction, ground_truth)))
    print("EM removed comment".ljust(20, ' '), ':', calc_em_removed_comment(prediction, ground_truth))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    args = parser.parse_args()
    main(args)