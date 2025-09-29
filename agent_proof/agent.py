from agent_proof.gen_proof import get_proof_current_theorem, regenerate_proof
from agent_proof.proof import prove, prove_backtrack, prove_hammer_first
from utils_coq import parse_response_proof
from typing import Any
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import ProofTerm, Step
from coqpyt.coq.changes import ProofPop


def prove_theorem(proof_file: ProofFile, proof_term: ProofTerm, steps: list[Step], method: str = 'hammer_dsp') -> tuple[bool, dict[str, Any], str, str, str, str]:
    # clear the existing proof, if 
    if len(proof_term.steps) > 0:   
        changes_clear = [ProofPop() for _ in range(len(proof_term.steps))]
        proof_file.change_proof(proof_term, changes_clear)

    if method == 'palm':
        success, log_prove = prove_backtrack(proof_file, proof_term, steps)
    elif method == 'hammer_dsp':
        success, log_prove = prove_hammer_first(proof_file, proof_term, steps)
    elif method == 'dsp':
        success, log_prove = prove(proof_file, proof_term, steps)
    else:
        raise ValueError(f'Invalid method: {method}')

    # partial_proof = [s.text for s in proof_term.steps]
    # partial_proof_str = ''.join(partial_proof)
    partial_proof_str = log_prove['final_proof']
    if success:
        stuck_state = ''
        error_tactic = ''
        error_msg = ''
    else:
        stuck_state = log_prove['stuck_state']
        error_tactic = log_prove['error_tactic']
        error_msg = log_prove['error_msg']
        # assert len(proof_file.current_goals.goals.goals) > 0, proof_file.path + ' ' + proof_term.step.text + '\n' + ''.join([s.text for s in proof_term.steps])
        # proof_state = proof_file.current_goals.goals.goals[0]
        # goal_str = format_goal(proof_state)
    return success, log_prove, partial_proof_str, stuck_state, error_tactic, error_msg


def prove_theorem_raw_response(proof_file: ProofFile, proof_term: ProofTerm, raw_response: str, method: str = 'hammer_dsp') -> tuple[bool, str, str, str, str, str, list[dict], dict[str, Any], dict[str, Any]]:
    steps = parse_response_proof(raw_response)
    full_proof_str = ''.join([s.text for s in steps])
    success, log_prove, partial_proof_str, stuck_state, error_tactic, error_msg = prove_theorem(proof_file, proof_term, steps, method)
    return success, full_proof_str, partial_proof_str, stuck_state, error_tactic, error_msg, log_prove


def prove_theorem_initial(proof_file: ProofFile, proof_term: ProofTerm, theorem: str, definitions: dict[str, str] | list[str], reuse_path: str = '', method: str = 'hammer_dsp') -> tuple[bool, str, str, str, str, str, list[dict], dict[str, Any], dict[str, Any]]:
    steps, log_proof_gen, conversation = get_proof_current_theorem(theorem, definitions, [], reuse_path)
    full_proof_str = ''.join([s.text for s in steps])
    success, log_prove, partial_proof_str, stuck_state, error_tactic, error_msg = prove_theorem(proof_file, proof_term, steps, method)
    return success, full_proof_str, partial_proof_str, stuck_state, error_tactic, error_msg, conversation, log_proof_gen, log_prove


def prove_theorem_initial_w_lemmas(proof_file: ProofFile, proof_term: ProofTerm, theorem: str, definitions: dict[str, str] | list[str], lemmas: list[str], reuse_path: str = '', method: str = 'hammer_dsp') -> tuple[bool, str, str, str, str, str, list[dict], dict[str, Any], dict[str, Any]]:
    steps, log_proof_gen, conversation = get_proof_current_theorem(theorem, definitions, lemmas, reuse_path)
    full_proof_str = ''.join([s.text for s in steps])
    success, log_prove, partial_proof_str, stuck_state, error_tactic, error_msg = prove_theorem(proof_file, proof_term, steps, method)
    return success, full_proof_str, partial_proof_str, stuck_state, error_tactic, error_msg, conversation, log_proof_gen, log_prove


def prove_theorem_regenerate(proof_file: ProofFile, proof_term: ProofTerm, proof_state: str, theorem: str, error_tactic: str, error_msg: str, partial_proof: str, definitions: dict[str, str] | list[str], lemmas: dict[str, str] | list[str], similar_proof: str, method: str = 'hammer_dsp') -> tuple[bool, str, str, str, str, str, list[dict], dict[str, Any], dict[str, Any]]:
    steps, log, conversation = regenerate_proof(theorem, partial_proof, proof_state, error_tactic, error_msg, definitions, lemmas, similar_proof)
    full_proof_str = ''.join([s.text for s in steps])
    success, log_prove, partial_proof_str, stuck_state, error_tactic, error_msg = prove_theorem(proof_file, proof_term, steps, method)
    return success, full_proof_str, partial_proof_str, stuck_state, error_tactic, error_msg, conversation, log, log_prove
