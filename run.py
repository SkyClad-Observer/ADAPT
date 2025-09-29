from typing import Any
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.base_file import CoqFile
from coqpyt.coq.structs import Step
import shutil
import multiprocessing
import os
import argparse
import re
from path import DATASET, DATASET_NO_DEPS, LOG
from utils import get_coq_project_info_from_file, copy_file, json_load
from main.framework import prove_llm_simpl_new
from llm import LLM
import json


def get_targets(proj: str) -> tuple[dict[str, dict], dict[str, str]]:
    eval_commits_path = os.path.join(DATASET, proj, 'eval_commits.jsonl')
    eval_commits = []
    with open(eval_commits_path, 'r') as f:
        for line in f:
            commit = json.loads(line)['commit_sha']
            eval_commits.append(commit)
            
    total_count = 0
    target_path = os.path.join(DATASET, proj, 'eval_commits_theorems.json')
    targets = json_load(target_path)
    targets = {commit: targets[commit] for commit in eval_commits}

    metadata_path = os.path.join(DATASET, proj, 'meta.json')
    commits_info = json_load(metadata_path)['commits_info']
    parent_commits = {commit: commits_info[commit]['parent'] for commit in targets}

    for commit, file_to_theorems in targets.items():
        total_count += sum([len(theorems) for theorems in file_to_theorems.values()])
    print(f'Total number of theorems: {total_count}')
    
    return targets, parent_commits


def copy_resume_log(exp_name: str, proj: str, commit: str, file_name: str, resume: str):
    log_resume_path = os.path.join('./log', resume, proj, commit, file_name)
    log_exp_path = os.path.join('./log', exp_name, proj, commit, file_name)
    if not os.path.exists(log_exp_path):
        os.makedirs(log_exp_path)
    if not os.path.exists(log_resume_path):
        print(f'Log resume path {log_resume_path} does not exist')
        return
    
    thms = os.listdir(log_resume_path)
    for thm in thms:
        thm_log_path = os.path.join(log_resume_path, thm)
        thm_log = json_load(thm_log_path)
        succ = thm_log[0]['success']
        if succ:
            shutil.copy(thm_log_path, os.path.join(log_exp_path, thm))


def get_existing_logs(exp_name: str, proj: str, commit: str, file: str) -> set[str]:
    log_poj_path = os.path.join(LOG, exp_name, proj, commit, file)
    if not os.path.exists(log_poj_path):
        return set()
    thms = os.listdir(log_poj_path)
    results = set()
    for thm in thms:
        thm_name = thm.replace('.json', '')
        results.add(file + '/' + thm_name)
    return results


def get_theorem_name(text: str) -> str:
    NAME_PATTERN = re.compile(r"\S+\s+(\S+?)[\[\]\{\}\(\):=,\s]")
    name_match = NAME_PATTERN.search(text)
    if name_match is not None:
        (name,) = name_match.groups()
        return name
    

def is_begin_of(step: Step, thm: dict[str, Any]) -> bool:
    short_text = step.short_text.strip()
    text = step.text.strip()
    return thm['text'] == short_text or thm['text'] == text
    # step_name = get_theorem_name(step.text.strip())
    # thm_name = thm['name']
    # return step_name == thm_name


def is_begin_any(step: Step, thms: list[dict[str, Any]]) -> bool:
    for thm in thms:
        if is_begin_of(step, thm):
            return True
    return False


def is_abort(steps: list[Step], ind: int) -> int:
    if ind + 1 < len(steps) and steps[ind + 1].short_text.strip() == 'Abort.':
        return 1
    elif ind + 2 < len(steps) and steps[ind + 2].short_text.strip() == 'Abort.':
        return 2
    return 0


def prove_one_thm(exp_name: str, workspace: str, proj: str, commit: str, parent_commit: str, file: str, task: dict, tasks: list[dict], resume: str = ''):  
    file_path = os.path.join(workspace, file)
    option = get_coq_project_info_from_file(file_path)
    with CoqFile(file_path, workspace=workspace, timeout=600, extra_options=option) as coq_file:
        steps = coq_file.steps

    partial_steps = []
    ind = 0
    while ind < len(steps):
        step = steps[ind]
        if is_begin_any(step, tasks):
            if is_begin_of(step, task):
                partial_steps.append(step)
                break
            else:
                abt = is_abort(steps, ind)
                if abt > 0:
                    ind += abt + 1
                else:
                    partial_steps.append(step)
                    ind += 1
        else:
            partial_steps.append(step)
            ind += 1

    if ind == len(steps):
        print(f'Theorem {task["name"]} not found in {file}')
        return
    
    partial_steps_text = ''.join([step.text for step in partial_steps])
    hammer_time = 10
    
    partial_steps_text = f'From Hammer Require Import Hammer.\nSet Hammer ATPLimit {hammer_time}.\n' + partial_steps_text

    copied_file = copy_file(file_path, content = partial_steps_text)
    try:
        use_disk_cache = True
        with ProofFile(copied_file, use_disk_cache=use_disk_cache, workspace=workspace, timeout=600, error_mode='warning', extra_options=option) as proof_file:
            proof_file.run()
            assert proof_file.is_valid
            assert proof_file.in_proof
            proof_term = proof_file.open_proofs[-1]
            assert is_begin_of(proof_term.step, task)
            proof_file.append_step(proof_term, '\nProof.')
            success, log = prove_llm_simpl_new(exp_name, proof_file, proof_term, proj, commit, file, resume)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Error: ', file, task['name'])
        print(e)
    finally:
        os.remove(copied_file)


def prove_project(exp_name: str, proj: str, resume: str, processes: int):
    eval_targets, parent_commits = get_targets(proj)
    all_tasks = []
    all_thms = []

    for commit, file_to_theorems in eval_targets.items():
        parent_commit = parent_commits[commit]
        workspace = os.path.join(DATASET_NO_DEPS, proj, commit, proj)
        for file, theorems in file_to_theorems.items():
            if resume:
                copy_resume_log(exp_name, proj, commit, file, resume)
            existing_logs = get_existing_logs(exp_name, proj, commit, file)
            theorems_unsolved = [thm for thm in theorems if file + '/' + thm['name'] not in existing_logs]
            if len(theorems_unsolved) == 0:
                continue
            for thm in theorems_unsolved:
                all_tasks.append((exp_name, workspace, proj, commit, parent_commit, file, thm, all_thms, resume))
                all_thms.append(thm)

    all_tasks.sort(key=lambda x: x[4] + '/' + x[6] + '/' + x[7]['name'])
    
    print(f'Remaining tasks: {len(all_tasks)}')
    if processes == 1:
        for task in all_tasks:
            prove_one_thm(*task) 
    else:
        pool = multiprocessing.Pool(processes=processes)
        pool.starmap(prove_one_thm, all_tasks)
        pool.close()
        pool.join()


if __name__ == '__main__':
    # sys.setrecursionlimit(2048)
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_name', type=str)
    parser.add_argument('--proj', type=str)
    parser.add_argument('--model', type=str, choices=['gpt-4o', 'gpt-4o-mini', 'deepseek-chat', 'claude-3-7-sonnet-20250219', 'meta-llama/llama-4-maverick-17b-128e-instruct-fp8'])
    parser.add_argument('--temp', type=float, default=0)
    parser.add_argument('--top_p', type=float, default=1)
    parser.add_argument('--resume', type=str, default='')
    parser.add_argument('--processes', type=int, default=1)
    args = parser.parse_args()

    LLM.model = args.model
    LLM.temp = args.temp
    LLM.top_p = args.top_p
    prove_project(args.exp_name, args.proj, args.resume, args.processes)
