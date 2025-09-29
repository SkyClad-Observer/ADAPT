from agent_lemma.propose_lemma import get_lemmas_for_state
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import ProofTerm
from typing import Any
from agent_lemma.prove_lemma import prove_lemmas
from agent_lemma.refine_lemma import refine_lemma, validate_lemmas

# refer to this function for the process of lemma discovery
def lemma_discovery(proof_file: ProofFile, proof_term: ProofTerm, helper_lemmas: dict[str, str], reuse_path: str = '', method: str = 'hammer_dsp') -> tuple[dict[str, str], list[str], dict[str, Any]]:
    # propose new lemmas
    new_lemmas, log_propose_lemmas = get_lemmas_for_state(proof_file, proof_term, helper_lemmas, reuse_path=reuse_path)

    # prove newly proposed lemmas
    if new_lemmas:
        success_lemmas, failed_lemmas, log_prove_lemmas = prove_lemmas(proof_file, proof_term, new_lemmas, helper_lemmas, method=method)
    else:
        success_lemmas, failed_lemmas, log_prove_lemmas = {}, [], {}
    log = {
        'propose_lemmas': {
            'lemmas': new_lemmas,
            'conversation': log_propose_lemmas,
        },
        'prove_lemmas': {
            'success_lemmas': success_lemmas,
            'failed_lemmas': failed_lemmas,
            'execution': log_prove_lemmas,
        },
    }
    return success_lemmas, failed_lemmas, log


def lemma_refinement(proof_file: ProofFile, proof_term: ProofTerm, theorem: str, previous_definitions: list[str], current_definitions: list[str], previous_lemmas: dict[str, str]) -> tuple[dict[str, str], list[str], dict[str, Any]]:
    refined_lemmas, conversation = refine_lemma(theorem, previous_definitions, current_definitions, previous_lemmas)
    success_lemmas, failed_lemmas, log_validate_lemmas = validate_lemmas(proof_file, proof_term, refined_lemmas)
    log = {
        'refine_lemmas': {
            'lemmas': refined_lemmas,
            'conversation': conversation,
        },
        'validate_lemmas': {
            'success_lemmas': success_lemmas,
            'failed_lemmas': failed_lemmas,
            'execution': log_validate_lemmas,
        },
    }
    return success_lemmas, failed_lemmas, log

