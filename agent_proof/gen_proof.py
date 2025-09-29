import os
import json
from typing import Any

from agent_proof.prompt import INITIAL_PROOF_WITH_LEMMAS, INITIAL_PROOF_WO_LEMMAS, REGENERATE_WITH_LEMMAS, REGENERATE_WO_LEMMAS, REGENERATE_WITH_LEMMAS_NEW, REGENERATE_WO_LEMMAS_NEW
from llmproof.utils import extract_code_blocks
from utils_coq import parse_response_proof, parse_code, remove_comments
from llm import LLM
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import Step, ProofTerm
from coqpyt.coq.changes import ProofPop


def clear_proof(proof_file: ProofFile, proof_term: ProofTerm):
    changes = [ProofPop() for _ in range(len(proof_term.steps))]
    proof_file.change_proof(proof_term, changes)


def _parse_response_proof_refine(response: str, previous_proof: str) -> list[Step]:
    blocks = extract_code_blocks(response.strip())
    if len(blocks) == 0:
        return []
    code = blocks[-1].strip()
    if 'no change' in code.lower() and 'Qed' not in code:
        code = previous_proof
    code = remove_comments(code)
    steps = parse_code(code) # coq_file.parse_code('\n\n' + code)
    for i in range(len(steps)):
        if steps[i].short_text == 'Proof.':
            return steps[i+1:]
    return steps
        

def get_proof_current_theorem(theorem: str, definitions: list[str], lemmas: list[str], reuse_path: str = '') -> tuple[list[Step], dict[str, Any], list[dict]]:
    if reuse_path:
        log_path = os.path.join(reuse_path, 'initial_proof.json')
        if os.path.exists(log_path):
            try:
                log = json.load(open(log_path, 'r'))
                prompt = log['prompt']
                response = log['response']
                conversation = [
                    {'role': 'user', 'content': prompt},
                    {'role': 'assistant', 'content': response}
                ]
                return parse_response_proof(response), log, conversation
            except Exception as e:
                pass

    log = {}
    log['theorem'] = theorem
    log['definitions'] = definitions
    log['lemmas'] = lemmas

    definitions_str = '\n\n'.join([text for text in definitions])
    if lemmas:
        lemmas_str = '\n\n'.join(lemmas)
        prompt = INITIAL_PROOF_WITH_LEMMAS.format(theorem=theorem, definitions=definitions_str, lemmas=lemmas_str)
    else:
        prompt = INITIAL_PROOF_WO_LEMMAS.format(theorem=theorem, definitions=definitions_str)

    llm = LLM()
    response = llm.query(prompt, append = True)[0]
    steps = parse_response_proof(response)
    log['prompt'] = prompt
    log['response'] = response
    log['steps'] = [s.text for s in steps]
    return steps, log, llm.conversation


def regenerate_proof(theorem: str, partial_proof: str, proof_state: str, error_tactic: str, error_msg: str, definitions: dict[str, str] | list[str], lemmas: dict[str, str] | list[str], similar_proof: str) -> tuple[list[Step], dict[str, Any], list[dict]]:
    llm = LLM()
    if isinstance(definitions, dict):
        definitions_str = '\n\n'.join([text for text in definitions.values()])
    else:
        definitions_str = '\n\n'.join(definitions)
    if isinstance(lemmas, dict):
        lemmas_str = '\n\n'.join([lemma for _, lemma in lemmas.items()])
    else:
        lemmas_str = '\n\n'.join(lemmas)
    if lemmas:
        prompt = REGENERATE_WITH_LEMMAS.format(theorem=theorem, partial_proof=partial_proof, proof_state=proof_state, error_tactic=error_tactic, error_msg=error_msg, definitions=definitions_str, lemmas=lemmas_str, similar_proof=similar_proof)
    else:
        prompt = REGENERATE_WO_LEMMAS.format(theorem=theorem, partial_proof=partial_proof, proof_state=proof_state, error_tactic=error_tactic, error_msg=error_msg, definitions=definitions_str, lemmas=lemmas_str, similar_proof=similar_proof)

    response = llm.query(prompt)[0]
    steps = parse_response_proof(response)
    log = {
        'theorem': theorem,
        'partial_proof': partial_proof,
        'proof_state': proof_state,
        'definitions': definitions,
        'lemmas': lemmas,
        'steps': [s.text for s in steps],
        'prompt': prompt,
        'response': response
    }
    return steps, log, llm.conversation
