import numpy as np
from rank_bm25 import BM25Okapi
from ..utils_coq import normalize_spaces, get_ids_in_step, get_ids_in_step_recursive
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import Term, Step, ProofTerm, TermType
from coqpyt.coq.lsp.structs import Goal, Hyp


def predict(proof_file: ProofFile, proof_term: ProofTerm, num: int = 200, remove_std: bool = True, thm_only: bool = True) -> dict[str, Term]:
    # tactic = '\nProof.'
    tactic = f'\npredict {num}.'
    try:
        proof_file.append_step(proof_term, tactic)
    except Exception as e:
        print(e)
        return {}
    step = proof_term.steps[-1]
    message = step.diagnostics[-1].message
    proof_file.pop_step(proof_term)

    results = message.split(', ')
    results_simplified = {}
    for name in results:
        if remove_std and name.startswith('Coq.'):
            continue

        sub_names = name.split('.')
        if name not in proof_file.context.terms:
            for i in range(len(sub_names)):
                sub_name = '.'.join(sub_names[i:])
                if sub_name in proof_file.context.terms:
                    name = sub_name
                    break
        if name not in proof_file.context.terms:
            continue

        term = proof_file.context.terms[name]

        for i in range(1, len(sub_names)+1):
            sub_name = '.'.join(sub_names[-i:])
            if sub_name in proof_file.context.terms and proof_file.context.terms[sub_name] == term:
                results_simplified[sub_name] = term
                break
    
    to_remove = []
    for name, term in results_simplified.items():
        if thm_only and term.type not in [TermType.THEOREM, TermType.LEMMA, TermType.COROLLARY, TermType.NOTATION, TermType.TACTIC]:
            to_remove.append(name)
    for name in to_remove:
        results_simplified.pop(name)
    return results_simplified


def bm25(contexts, sp=' '):
    corpus = [s.split(sp) for s in contexts]
    bm25 = BM25Okapi(corpus)
    def query(q: str, top=300):
        q = q.split(sp)
        scores = bm25.get_scores(q)
        top_indices = np.argsort(scores)[::-1][:top]
        top_contexts = [contexts[i] for i in top_indices]
        return top_contexts
    return query


def generate_query(goal: Goal) -> str:
    goal_ty = goal.ty
    hyps_ty = [h.ty for h in goal.hyps]
    hyps_ty.append(goal_ty)
    return ' -> '.join(hyps_ty)
    

def retrieve_hammer(proof_file: ProofFile, proof_term: ProofTerm, top: int) -> tuple[list[str], dict[str, str]]:
    # defs = get_ids_in_step_recursive(proof_file, proof_term.step) 
    predicted_premises = predict(proof_file, proof_term, top*6)
    context = {name: term.step.short_text for name, term in predicted_premises.items()}
    context_list = list(context.values())
    if len(context_list) == 0:
        return [], {}
    query = generate_query(proof_file.current_goals.goals.goals[0])
    query_bm25 = bm25(context_list)
    res = query_bm25(query)
    return res, context


if __name__ == '__main__':
    pass
