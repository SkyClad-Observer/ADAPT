import os
import json
from typing import Any
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import Term, Step, ProofTerm
from coqpyt.coq.proof_file import ProofPop
from agent_proof.agent import prove_theorem
from agent_proof.gen_proof import get_proof_current_theorem
from utils_coq import get_ids_in_step_recursive


def prove_lemmas(proof_file: ProofFile, original_proof_term: ProofTerm, lemmas_to_prove: dict[str, dict], helper_lemmas: dict[str, str], method: str = 'hammer_dsp') -> tuple[dict[str, str], list[str], dict[str, Any]]:
    success_lemmas = {}
    failed_lemmas = []
    lemmas_log = {}

    # abort the original proof
    proof_file.append_step(original_proof_term, '\nAbort.')

    for name, lemma in lemmas_to_prove.items():
        if name in helper_lemmas:
            continue
        proof_term = None
        lemma, complete = lemma['text'], lemma['complete']
        start_index = proof_file.find_step_index(original_proof_term.ast.range) - 1
        for code in complete:
            proof_file.add_step(start_index, f'\n{code}')
            proof_file.exec(1)
        assert proof_file.in_proof
        for open_thm in proof_file.open_proofs:
            if open_thm.text.strip() == lemma.strip():
                proof_term = open_thm
                break
        
        theorem_str = proof_term.step.short_text
        definitions = get_ids_in_step_recursive(proof_file, proof_term)
        definitions = {name: term.step.short_text.strip() for name, term in definitions.items()}
        definitions_list = list(set(definitions.values()))
        helper_lemmas_list = list(helper_lemmas.values())

        initial_proof_steps, log_initial_proof, conversation = get_proof_current_theorem(theorem_str, definitions_list, helper_lemmas_list)
        success, log_prove, partial_proof_str, goal_str, error_tactic, error_msg = prove_theorem(proof_file, proof_term, initial_proof_steps, method=method)
        log_initial_proof['execution'] = log_prove
        lemmas_log[name] = {
            'conversation': conversation,
            'execution': log_prove,
        }

        if success:
            success_lemmas[name] = proof_term.step.short_text.strip()
            helper_lemmas[name] = lemma
            assert proof_term.steps[-1].step.short_text == 'Qed.', proof_term.steps[-1].step.short_text
        else:
            changes_clear = [ProofPop() for _ in proof_term.steps]
            proof_file.change_proof(proof_term, changes_clear)
            failed_index = proof_file.find_step_index(proof_term.ast.range)
            proof_file.delete_step(failed_index)
            failed_lemmas.append(name)
            proof_term = None
        print('Prove lemma: ', name, success)
        assert not proof_file.in_proof

    lemmas_log['success_lemmas'] = success_lemmas
    lemmas_log['failed_lemmas'] = failed_lemmas

    assert not proof_file.in_proof
    for unproven in proof_file.unproven_proofs:
        if not 0 < len(unproven.steps) < 3:
            print(unproven.text)
            for step in unproven.steps:
                print(step.step.short_text)
            assert False

    proof_file.pop_step(original_proof_term)

    return success_lemmas, failed_lemmas, lemmas_log

