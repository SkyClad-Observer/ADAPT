import os
import json
from typing import Any
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.base_file import CoqFile
from coqpyt.coq.structs import Term, ProofTerm
from coqpyt.coq.lsp.structs import Goal

from utils_coq import *
from llm import LLM
from agent_lemma.prompt import *


def get_ids_from_goal(proof_file: ProofFile, proof_term: ProofTerm, goal: Goal) -> dict[str, Term]:
    goal = proof_file.current_goals.goals.goals[0]
    definitions = get_ids_in_step_recursive(proof_file, goal.ty)
    for hyp in goal.hyps:
        definitions.update(get_ids_in_step_recursive(proof_file, hyp.ty))
    return definitions


def get_lemmas_for_state(proof_file: ProofFile, proof_term: ProofTerm, helper_lemmas: dict[str, str], reuse_path: str = '') -> tuple[dict[str, dict], dict[str, Any]]:
    if reuse_path:
        log_path = os.path.join(reuse_path, 'lemmas.json')
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log = json.load(f)
                return log['lemmas']['compile_correct_lemmas'], log

    log = {}

    goal = proof_file.current_goals.goals.goals[0]
    definitions = get_ids_from_goal(proof_file, proof_term, goal)
    definitions = {name: term.step.short_text.strip() for name, term in definitions.items()}

    log['definitions'] = definitions
    
    goal_format = format_goal(goal)
    log['goal'] = goal_format 

    definitions_set = {text for _, text in definitions.items()}
    definitions_str = '\n\n'.join([text for text in definitions_set])
    
    if len(helper_lemmas) > 0:
        lemmas_str = '\n\n'.join(helper_lemmas.values())
        prompt = PROPOSE_LEMMAS_WITH_LEMMAS.format(definitions=definitions_str, proof_state=goal_format, lemmas=lemmas_str)
    else:
        prompt = PROPOSE_LEMMAS_WO_LEMMAS.format(definitions=definitions_str, proof_state=goal_format)

    llm = LLM()
    response = llm.query(prompt)[0]

    log['prompt'] = prompt
    log['response'] = response

    compile_correct_lemmas, compile_error_lemmas = parse_lemmas(proof_file, response)
    log['lemmas'] = {'compile_correct_lemmas': compile_correct_lemmas, 'compile_error_lemmas': compile_error_lemmas}
    return compile_correct_lemmas, log


def parse_lemmas(coq_file: CoqFile, response: str) -> tuple[dict[str, str], dict[str, str]]:
    blocks = extract_code_blocks(response.strip())
    compile_correct = {}
    compile_error = {}
    for block in blocks:
        if 'Proof.' in block:
            block = block[:block.find('Proof.')].strip()
        block = remove_comments(block)
        block = block.strip()
        codes = coq_file.parse_code('\n' + block)
        codes_text = [c.short_text for c in codes]
        lemma = codes_text[-1]
        if not (lemma.strip().startswith('Lemma ') or lemma.strip().startswith('Theorem ')):
            # syntax error
            for code in codes_text:
                if code.strip().startswith('Lemma ') or code.strip().startswith('Theorem '):
                    name = code.split()[1].strip()
                    break
            compile_error[name] = {'complete': codes_text, 'err_msgs': [c.diagnostics[-1].message for c in codes]}
        else:
            lemma = codes[-1]
            name = lemma.short_text.split()[1].strip()
            # complie error
            if lemma.diagnostics:
                err_msgs = [c.message for c in lemma.diagnostics]
                print(err_msgs)
                compile_error[name] = {'text': lemma.short_text, 'complete': codes_text, 'err_msgs': err_msgs}
            else:
                compile_correct[name] = {'text': lemma.short_text, 'complete': codes_text}
    return compile_correct, compile_error


if __name__ == '__main__':
    pass