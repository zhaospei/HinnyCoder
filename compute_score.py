#!/usr/bin/env python
# !-*-coding:utf-8 *

import argparse
import json
import logging
import sys
import warnings

import editdistance
import numpy as np

sys.path.append("metric")
from metric.smooth_bleu import codenn_smooth_bleu
from metric.rouge.rouge import Rouge

warnings.filterwarnings('ignore')
logging.basicConfig(format='[%(asctime)s - %(levelname)s - %(name)s] %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)

def em_prec_recall(refs, preds):
    EM = []

    for r, p in zip(refs, preds):
        EM.append(r[0] == p)
    
    print("EM: ", round(np.mean(EM)*100, 2))


def Commitbleus(refs, preds):
    r_str_list = []
    p_str_list = []
    for r, p in zip(refs, preds):
        if len(r[0]) == 0 or len(p) == 0:
            continue
        r_str_list.append([" ".join([str(token_id) for token_id in r[0]])])
        p_str_list.append(" ".join([str(token_id) for token_id in p]))
    # print(r_str_list)
    # print(p_str_list)
    try:
        bleu_list = codenn_smooth_bleu(r_str_list, p_str_list)
    except:
        bleu_list = [0, 0, 0, 0]
    codenn_bleu = bleu_list[0]

    B_Norm = round(codenn_bleu, 4)

    return B_Norm


def read_to_list(filename, index):
    f = open(filename, 'r',encoding="utf-8")
    res = []
    for row in f:
        if index:
            (rid, text) = row.split('\t')
            res.append(text.lower().split())
        else:
            res.append(row.lower().split())
    return res

def metetor_rouge_cider(refs, preds):

    refs_dict = {}
    preds_dict = {}
    for i in range(len(preds)):
        preds_dict[i] = [" ".join(preds[i])]
        refs_dict[i] = [" ".join(refs[i][0])]

    score_Rouge, scores_Rouge = Rouge().compute_score(refs_dict, preds_dict)
    print("Rouge-L: ", round(score_Rouge*100,2))

def compute_ES(target, predictions, passk):
    # print(target)
    # target_lines = [line.strip() for line in target.splitlines() if line.strip()]
    # target_str = '\n'.join(target_lines)
    target_str = target
    ES_scores = []
    for prediction in predictions[:passk]:
        # prediction_lines = [line.strip() for line in prediction.splitlines() if line.strip()][:len(target_lines)]
        # prediction_str = '\n'.join(prediction_lines)
        prediction_str = ' '.join(prediction)
        # print(target_str, prediction_str)
        ES_scores.append(
            1 - (editdistance.eval(target_str, prediction_str) / max(len(target_str), len(prediction_str)))
        )
    return max(ES_scores)

def compute_score_by_repo_with_metadata(refs, preds, passk=1):
    ES_scores = []
    
    for r, p in zip(refs, preds):
        # print(' '.join(r[0]))
        ES_scores.append(compute_ES(' '.join(r[0]), [p], passk))
    
    avg_scores = round(sum(ES_scores) / len(ES_scores) * 100, 2)
    
    print("ES: ", avg_scores)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prd_dir", default=None, type=str,
                        help="File dir to read predict msg")
    parser.add_argument("--gold_dir", default=None, type=str,
                        help="File dir to read gold msg")
    parser.add_argument("--prd_index", action='store_true',
                        help="Contain row id in file predict lines")
    parser.add_argument("--gold_index", action='store_true',
                        help="Contain row id in file gold lines")
    args = parser.parse_args()
    refs = read_to_list(args.gold_dir, args.gold_index)
    refs = [[t] for t in refs]
    preds = read_to_list(args.prd_dir, args.prd_index)
    bleus_score = Commitbleus(refs, preds)
    print("Refs: ", len(refs))
    print("Preds: ", len(preds))
    print("BLEU: %.2f"%bleus_score)
    metetor_rouge_cider(refs, preds)
    em_prec_recall(refs, preds)
    compute_score_by_repo_with_metadata(refs, preds)


if __name__ == '__main__':
    main()
