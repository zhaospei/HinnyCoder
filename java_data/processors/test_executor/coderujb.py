import os
import random
import re
import signal
import string
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import chardet
import javalang
import numpy as np
from tqdm import tqdm


# os.environ["TOKENIZERS_PARALLELISM"] = "true"

class CodeUJBComplete():
    """A task represents an entire benchmark including its dataset, problems,
    answers, generation settings and evaluation methods.
    """
    def evaluate(self, generations):
        """Takes the list of LM generations and evaluates them against ground truth references,
        returning the metric for the generations.
        Args:
            param generations list(list(str)): list of lists containing generations
            param references list(str): list of str containing refrences
        """
        all_tasks = []
        results = {"total": 0, "pass_syntax": {"count": 0}, "pass_compile": {"count": 0}, 
                   "pass_trigger": {"count": 0}, "pass_all": {"count": 0}, "timed_out": 0, "detail": {}}
        total_tokens_dict = {}
        for _, generation in tqdm(generations.iterrows(), total=len(generations)):
            idx = generation["task_idx"]
            gens = generation["outputs"]
            project = generation["project"]
            bug_id = generation["bug_id"]
            testmethods = generation["testmethods"]
            source_dir = generation["source_dir"]
            start = generation["start"]
            end = generation["end"]
            location = generation["location"]
            source = generation["source"]
            
            one_tasks = [(idx, gen, project, bug_id, testmethods, source_dir, 
                      start, end, location, source) for gen in gens]
            all_tasks.extend(one_tasks)
        
        with ProcessPoolExecutor(max_workers=os.cpu_count()//4) as executor:
            # Submit all your tasks to the executor
            future_tasks = set()
            for task in all_tasks:
                future_tasks.add(executor.submit(validate_all_patches, task))
                time.sleep(0.01)
            # Use tqdm to display progress
            all_bug_results_list = []
            with tqdm(as_completed(future_tasks), total=len(all_tasks), desc="Evaluating all tasks...") as progress_bar:
                for future in progress_bar:
                    # Append the result to a list
                    all_bug_results_list.append(future.result())
        
        all_bug_results_dict = {}
        for bug_result in all_bug_results_list:
            if bug_result["idx"] not in all_bug_results_dict:
                all_bug_results_dict[bug_result["idx"]] = []
            all_bug_results_dict[bug_result["idx"]].append(bug_result)
        
        keys_list = list(all_bug_results_dict.keys())
        keys_list.sort()
        for idx in keys_list:
            bug_results = all_bug_results_dict[idx]
            
            example_detail = {"total": 0, "total_tokens": total_tokens_dict[idx], 
                              "pass_syntax": {"count": 0}, "pass_compile": {"count": 0}, 
                              "pass_trigger": {"count": 0}, "pass_all": {"count": 0}, "timed_out": 0}
            for detail in bug_results:
                example_detail["total"] += 1
                if detail["pass_syntax"]:
                    example_detail["pass_syntax"]["count"] += 1
                if detail["pass_compile"]:
                    example_detail["pass_compile"]["count"] += 1
                if detail["pass_trigger"]:
                    example_detail["pass_trigger"]["count"] += 1
                if detail["pass_all"]:
                    example_detail["pass_all"]["count"] += 1
                if detail["timed_out"]:
                    example_detail["timed_out"] += 1
            
            for key in list(results.keys()):
                if not "pass" in key: continue
                for k in [1, 5, 10, 20, 50, 100]:
                    if example_detail["total"] < k: continue 
                    example_detail[key][f"pass@k-{k}"] = get_pass_at_k(example_detail["total"], example_detail[key]["count"], k)
                    if not f"pass@k-{k}" in results[key]:
                        results[key][f"pass@k-{k}"] = []
                    results[key][f"pass@k-{k}"].append(example_detail[key][f"pass@k-{k}"])
                for t in [1000, 5000, 10000, 20000, 500000, 1000000]:
                    if example_detail["total_tokens"] < t: continue 
                    tk = t / (example_detail["total_tokens"] / example_detail["total"])
                    example_detail[key][f"pass@t-{t}"] = get_pass_at_k(example_detail["total"], example_detail[key]["count"], tk)
                    if not f"pass@t-{t}" in results[key]:
                        results[key][f"pass@t-{t}"] = []
                    results[key][f"pass@t-{t}"].append(example_detail[key][f"pass@t-{t}"])
                
            print(example_detail)
            results["detail"][idx] = example_detail
            results["total"] += 1
            if example_detail["pass_syntax"]["count"] > 0:
                results["pass_syntax"]["count"] += 1
            if example_detail["pass_compile"]["count"] > 0:
                results["pass_compile"]["count"] += 1
            if example_detail["pass_trigger"]["count"] > 0:
                results["pass_trigger"]["count"] += 1
            if example_detail["pass_all"]["count"] > 0:
                results["pass_all"]["count"] += 1
            results["timed_out"] += example_detail["timed_out"]
        
        for key in list(results.keys()):
            if not "pass" in key: continue
            for pkey in list(results[key].keys()):
                if "@" in pkey:
                    results[key][pkey] = np.mean(results[key][pkey])
        return results
    
def get_pass_at_k(n, c, k):
    if n - c < k : return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

def read_file(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    encoding = chardet.detect(content)['encoding']
    decoded_content = content.decode(encoding)
    return decoded_content

def save_file(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def validate_all_patches(item):
    idx, patch, project, bug_id, testmethods, source_dir, start, end, location, source = item
    def generate_random_string(length):
        characters = string.ascii_letters + string.digits  # 包含大写字母、小写字母和数字
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string

    tmp_folder = f"{project}-{bug_id}-" + generate_random_string(16)
    subprocess.run(['rm', '-rf', '/tmp/' + tmp_folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    cmd = ['defects4j', 'checkout', '-p', project, '-v', str(bug_id) + 'f', '-w', '/tmp/' + tmp_folder]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    
    raw_source = source
    source = source.split("\n")
    patch = patch.split("\n")
    source = "\n".join(source[:start] + patch + source[end+1:])

    save_file("/tmp/" + tmp_folder + "/" + location, source)
    
    compile_fail, timed_out, bugg, entire_bugg, syntax_error = run_d4j_test(source, testmethods, tmp_folder)
        
    subprocess.run(['rm', '-rf', '/tmp/' + tmp_folder], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return {
            "idx": idx,
            "project": project,
            "bug_id":  bug_id,
            "pass_syntax": not syntax_error,
            "pass_compile": not compile_fail,
            "pass_trigger": not bugg,
            "pass_all": not entire_bugg,
            "timed_out": timed_out,
        }
    
def run_d4j_test(source: str, testmethods: List[str], bug_id: str):
    """
    Returns:
        [compile_fail, time_out, bug, entire_bug, syntax_error]
    """
    bugg = False
    compile_fail = False
    timed_out = False
    entire_bugg = True
    error_string = ""

    try:
        tokens = javalang.tokenizer.tokenize(source)
        parser = javalang.parser.Parser(tokens)
        parser.parse()
    except:
        # print("Syntax Error")
        return True, False, True, True, True

    for t in testmethods:
        # print(t.strip())
        cmd = 'defects4j test -w %s/ -t %s' % (('/tmp/' + bug_id), t.strip())
        Returncode = ""
        error_file = open("/tmp/stderr.txt", "wb")
        # print(cmd)
        child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=error_file, bufsize=-1,
                                start_new_session=True)
        while_begin = time.time()
        while True:
            Flag = child.poll()
            if Flag == 0:
                Returncode = child.stdout.readlines()  # child.stdout.read()
                # print(b"".join(Returncode).decode('utf-8'))
                error_file.close()
                break
            elif Flag != 0 and Flag is not None:
                compile_fail = True
                error_file.close()
                with open("/tmp/stderr.txt", "rb") as f:
                    r = f.readlines()
                for line in r:
                    if re.search(':\serror:\s', line.decode('utf-8')):
                        error_string = line.decode('utf-8')
                        break
                # print("error_string", error_string)
                break
            elif time.time() - while_begin > 120:
                error_file.close()
                os.killpg(os.getpgid(child.pid), signal.SIGTERM)
                timed_out = True
                break
            else:
                time.sleep(0.01)
        log = Returncode
        if len(log) > 0 and log[-1].decode('utf-8') == "Failing tests: 0\n":
            continue
        else:
            bugg = True
            break

    # Then we check if it passes all the tests, include the previously okay tests
    if not bugg:
        # print('So you pass the basic tests, Check if it passes all the test, include the previously passing tests')
        cmd = 'defects4j test -w %s/' % ('/tmp/' + bug_id)
        Returncode = ""
        child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1,
                                start_new_session=True)
        while_begin = time.time()
        while True:
            Flag = child.poll()
            if Flag == 0:
                Returncode = child.stdout.readlines()  # child.stdout.read()
                break
            elif Flag != 0 and Flag is not None:
                bugg = True
                break
            elif time.time() - while_begin > 180:
                os.killpg(os.getpgid(child.pid), signal.SIGTERM)
                bugg = True
                break
            else:
                time.sleep(0.01)
        log = Returncode
        if len(log) > 0 and log[-1].decode('utf-8') == "Failing tests: 0\n":
            entire_bugg = False

    return compile_fail, timed_out, bugg, entire_bugg, False