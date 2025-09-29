import re
from difflib import SequenceMatcher
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import Term, Step, ProofTerm, TermType
from coqpyt.coq.lsp.structs import Goal, Hyp
from agent_retrieval.dependency_graph_simple_rango_file import Graph, Thm, CtxTerm
from agent_retrieval.bm25 import bm25
from agent_retrieval.tfidf import tf_idf
from agent_retrieval.retrieve_hammer import retrieve_hammer
from agent_retrieval.tactics import all_tactics
from utils import json_load, json_dump, find_datapoint_dir_from_file
from utils_coq import remove_comments, get_ids_in_step_recursive, parse_response_proof, format_goal
from path import DATASET_NORMAL
import os


IDENT_PATTERN = re.compile(r'[a-zA-Z_][a-zA-Z0-9_\']*(?:\.[a-zA-Z_][a-zA-Z0-9_\']*)*')

def extract_identifiers_in_sentence(sentence: str):
    if not sentence:
        return []
    identifiers = IDENT_PATTERN.findall(sentence)

    results = set()
    for identifier in identifiers:
        if '.' in identifier:
            results.add(identifier.split('.')[-1])
        else:
            results.add(identifier)
    results = results.difference(all_tactics)
    return list(results)


def get_ids_from_goal(goal: Goal) -> tuple[list[str], list[str]]:
    goal_search_str = goal.ty
    hyp_search_str = ""
    h_ids: set[str] = set()
    for h in goal.hyps:
        h_ty = h.split(":")
        if len(h_ty) == 1:
            hyp_search_str += " " + h_ty[0]
        else:
            h_ids |= set(h_ty[0].split(", "))
            hyp_search_str += " " + "".join(h_ty[1:])
    hyp_found_ids = extract_identifiers_in_sentence(hyp_search_str)
    filtered_hyp_ids = [f for f in hyp_found_ids if f not in h_ids]
    goal_found_ids = extract_identifiers_in_sentence(goal_search_str)
    filtered_goal_ids = [f for f in goal_found_ids if f not in h_ids]
    return filtered_hyp_ids, filtered_goal_ids


def get_ids_from_goal(proof_file: ProofFile, proof_term: ProofTerm, goal: Goal) -> dict[str, Term]:
    goal = proof_file.current_goals.goals.goals[0]
    definitions = get_ids_in_step_recursive(proof_file, goal.ty)
    for hyp in goal.hyps:
        definitions.update(get_ids_in_step_recursive(proof_file, hyp.ty))
    return definitions


def get_goal_ids(goals: list[Goal]) -> list[str]:
    ids: list[str] = []
    for g in goals:
        hyp_ids, goal_ids = get_ids_from_goal(g)
        ids.extend(hyp_ids)
        ids.extend(goal_ids)
    return ids


def cal_similarity(thm1: str, name1: str, terms1: dict[str, str], thm2: str, name2: str, terms2: dict[str, CtxTerm]) -> float:
    if thm1 == thm2:
        return float('inf')
    
    name_sim = SequenceMatcher(None, name1, name2).ratio()

    term_names1 = set(terms1.keys())
    term_names2 = set(terms2.keys())
    common_names = term_names1.intersection(term_names2)
    all_names = term_names1.union(term_names2)

    term_sim = len(common_names) / len(all_names) if len(all_names) > 0 else 0

    thm_text_sim = SequenceMatcher(None, thm1, thm2).ratio()

    similarity = name_sim + term_sim + thm_text_sim
    return similarity


def retrieve_similar_theorems(theorem: str, theorem_name: str, definitions: dict[str, str], file_path: str, graph: Graph, top: int = 3) -> list[tuple[Thm, float]]:
    file_names = [file_graph.file_path for file_graph in graph.files_list]
    file_name_sims = [(file_name, SequenceMatcher(None, file_path, file_name).ratio()) for file_name in file_names]
    sorted_file_names = [file_name for file_name, _ in sorted(file_name_sims, key=lambda x: x[1], reverse=True)]
    top_file_names = sorted_file_names[:3]

    thm_sims = []
    top_graph_files = [file_graph for file_graph in graph.files_list if file_graph.file_path in top_file_names]
    for graph_file in top_graph_files:
        for thm in graph_file.all_theorems_list:
            if thm.name and thm.text:
                thm_terms = graph_file.get_terms_in_text_recursive(thm.text)
                sim = cal_similarity(theorem, theorem_name, definitions, thm.text, thm.name, thm_terms)
                thm_sims.append((thm, sim))
    
    thm_sims.sort(key=lambda x: x[1], reverse=True)
    top_thms = thm_sims[:top]
    return top_thms


def retrieve_similar_theorems_compare(theorem: str, theorem_name: str, definitions: dict[str, str], file_path: str, proj: str, commit: str, parent_commit: str, top: int = 3) -> tuple[Thm, Thm]:
    datapoint_path_parent = os.path.join(DATASET_NORMAL, proj, parent_commit, 'datapoint')
    datapoint_path_current = os.path.join(DATASET_NORMAL, proj, commit, 'datapoint')
    graph_parent = Graph.from_proj_datapoint(datapoint_path_parent, proj)
    graph_this = Graph.from_proj_datapoint(datapoint_path_current, proj)

    # old method
    file_names = [file_graph.file_path for file_graph in graph_this.files_list if file_graph.file_path != file_path]
    file_name_sims = [(file_name, SequenceMatcher(None, file_path, file_name).ratio()) for file_name in file_names]
    sorted_file_names = [file_name for file_name, _ in sorted(file_name_sims, key=lambda x: x[1], reverse=True)]
    top_file_names = sorted_file_names[:3]

    this_graph_file = graph_this.get_graph_file(file_path)
    terms_in_thm = this_graph_file.get_terms_in_text_recursive(theorem)

    thm_sims = []
    top_graph_files = [file_graph for file_graph in graph_this.files_list if file_graph.file_path in top_file_names]
    for graph_file in top_graph_files:
        for thm in graph_file.all_theorems_list:
            thm_terms = graph_file.get_terms_in_text_recursive(thm.text)
            sim = cal_similarity(theorem, theorem_name, terms_in_thm, thm.text, thm.name, thm_terms)
            thm_sims.append((thm, sim))
    
    thm_sims.sort(key=lambda x: x[1], reverse=True)
    top_thm = thm_sims[0][0]

    # new method
    top_thms_parent = retrieve_similar_theorems(theorem, theorem_name, definitions, file_path, graph_parent, top=top)
    top_thm_parent = top_thms_parent[0][0]

    # if top_thm.name != top_thm_parent.name:
    #     print('different: ', file_path, theorem_name, top_thm.name, top_thm_parent.name)

    return top_thm, top_thm_parent
