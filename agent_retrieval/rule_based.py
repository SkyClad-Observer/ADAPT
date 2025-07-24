import os
from difflib import SequenceMatcher
from .dependency_graph_simple_rango_file import Graph, CtxTerm, Thm
from ..path import *
from ..utils import json_load


def get_targets(proj: str) -> dict[str, dict]:
    removed_path = os.path.join(DATASET_META, proj + '.json')
    removed = json_load(removed_path)
    return removed


def get_similar_proof_file_name(commit_sha: str, thm_name: str) -> tuple[str, str]:
    file_path = '/home/minghai/data/LLMproof/LLMProof/case_study/types-and-proofs_perfect_context/perfect_context_proof.txt'
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split(' ')
            if parts[0] == commit_sha and parts[1] == thm_name:
                return parts[2].strip()+'.v', parts[3].strip()
    return None, None


def cal_similarity(thm1: str, name1: str, terms1: dict[str, CtxTerm], thm2: str, name2: str, terms2: dict[str, CtxTerm]) -> float:
    name_sim = SequenceMatcher(None, name1, name2).ratio()

    term_names1 = set(terms1.keys())
    term_names2 = set(terms2.keys())
    common_names = term_names1.intersection(term_names2)
    all_names = term_names1.union(term_names2)

    term_sim = len(common_names) / len(all_names)

    similarity = name_sim + term_sim 
    return similarity


def retrieve_similar_theorems(thm_str: str, thm_name: str, file_path: str, graph: Graph) -> list[Thm]:
    file_names = [file_graph.file_path for file_graph in graph.files_list if file_graph.file_path != file_path]
    file_name_sims = [(file_name, SequenceMatcher(None, file_path, file_name).ratio()) for file_name in file_names]
    sorted_file_names = [file_name for file_name, _ in sorted(file_name_sims, key=lambda x: x[1], reverse=True)]
    top_file_names = sorted_file_names[:3]
    # file_names_tokens = [file_name.replace('.v', '').split('.') for file_name in file_names]
    # file_name_tokens = file_path.split('.')
    # bm25_scores = bm25(file_name_tokens, file_names_tokens)
    # top_file_names = [file_names[i] for i in bm25_scores.argsort()[-3:][::-1]]

    this_graph_file = graph.get_graph_file(file_path)
    terms_in_thm = this_graph_file.get_terms_in_text_recursive(thm_str)

    thm_sims = []
    top_graph_files = [file_graph for file_graph in graph.files_list if file_graph.file_path in top_file_names]
    for graph_file in top_graph_files:
        for thm in graph_file.all_theorems_list:
            thm_terms = graph_file.get_terms_in_text_recursive(thm.text)
            sim = cal_similarity(thm_str, thm_name, terms_in_thm, thm.text, thm.name, thm_terms)
            thm_sims.append((thm, sim))
    
    thm_sims.sort(key=lambda x: x[1], reverse=True)
    top_thms = [thm for thm, _ in thm_sims[:3]]
    return top_thms


def main(proj: str):
    eval_targets = get_targets(proj)
    for commit, file_to_theorems in eval_targets.items():
        datapoint_path = os.path.join(DATASET_NORMAL, proj, commit, 'datapoint')
        graph = Graph.from_proj_datapoint(datapoint_path, proj)
        for file, theorems in file_to_theorems.items():
            for thm in theorems:
                thm_name, thm_str = thm['name'], thm['text']
                similar_file, similar_thm = get_similar_proof_file_name(commit, thm_name)
                similar_thms = retrieve_similar_theorems(thm_str, thm_name, file, graph)
                most_similar_thm = similar_thms[0]
                print(commit, thm_name, most_similar_thm.file_path, most_similar_thm.name)


if __name__ == '__main__':
    main('types-and-proofs')
