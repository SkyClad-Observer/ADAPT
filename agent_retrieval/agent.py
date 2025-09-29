from agent_retrieval.retrieve_proof import retrieve_similar_theorems
from agent_retrieval.retrieve_hammer import retrieve_hammer
from utils_coq import get_ids_in_step_recursive
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import ProofTerm, Term, TermType
from agent_retrieval.dependency_graph_simple_rango_file import Graph, Thm, CtxTerm


def retrieve_current_definitions(proof_file: ProofFile, proof_term: ProofTerm) -> tuple[dict[str, Term], list[str]]:
    definitions = get_ids_in_step_recursive(proof_file, proof_term)
    definitions = {name: term.step.short_text.strip() for name, term in definitions.items()}
    definitions_list = list(set(definitions.values()))
    return definitions, definitions_list


def retrieve_current_lemmas(proof_file: ProofFile, proof_term: ProofTerm, top: int=50) -> tuple[list[str], dict[str, str]]:
    return retrieve_hammer(proof_file, proof_term, top=top)


def retrieve_current_terms_by_name(proof_file: ProofFile, proof_term: ProofTerm, names: list[str], lemma_only: bool) -> dict[str, CtxTerm]:
    res = {}
    for name in names:
        term = proof_file.context.get_term(name)
        if term is None:
            continue
        if lemma_only and term.type not in [TermType.LEMMA, TermType.THEOREM]:
            continue
        res[name] = CtxTerm.from_term(term)
    return res


def retrieve_previous_similar_theorems(proof_file: ProofFile, proof_term: ProofTerm, file_path: str, graph: Graph) -> list[Thm]:
    return retrieve_similar_theorems(proof_file, proof_term, file_path, graph, top=2)


