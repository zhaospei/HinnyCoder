#!/usr/bin/env python
# !-*-coding:utf-8 -*-
import json
import numpy as np
import sys

sys.path.append("metric")
from metric.smooth_bleu import codenn_smooth_bleu
from metric.rouge.rouge import Rouge
import warnings
import argparse
import logging
# import prettytable as pt

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


if __name__ == '__main__':
    main()
