from utils import json_load, jsonl_load, list_dirs_rec
from CoqDev.build.build_proj import clone_and_build
from path import COQDEV
import os


def read_projs():
    projs = {}
    projs = list_dirs_rec(COQDEV)
    for proj in projs:
        proj_path = os.path.join(COQDEV, proj)
        eval_commits = jsonl_load(os.path.join(proj_path, 'eval_commits.jsonl'))
        all_theorems = json_load(os.path.join(proj_path, 'all_theorems.json'))
        projs[proj] = {
            'eval_commits': eval_commits,
            'all_theorems': all_theorems
        }
    return projs


def build_all():
    projs = read_projs()
    for proj, data in projs.items():
        eval_commits = data['eval_commits']
        for commit in eval_commits:
            clone_and_build(proj, commit)


if __name__ == '__main__':
    build_all()