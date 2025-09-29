from utils_coq import *
from llm import LLM
from agent_lemma.prompt import *

from agent_lemma.prompt import REFINE_LEMMAS
from agent_proof.agent import prove_theorem
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import ProofTerm, Step
from coqpyt.coq.proof_file import ProofPop
from coqpyt.coq.base_file import CoqFile

def parse_refine_lemmas(coq_file: CoqFile, response: str) -> tuple[str, str]:
    code_blocks = extract_code_blocks(response.strip())
    if len(code_blocks) == 0:
        return []
    block = code_blocks[0]
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
                return []
    else:
        lemma = codes[-1]
        name = lemma.short_text.split()[1].strip()
        return name, block


def refine_lemma(theorem: str, proof_state: str, definitions: list[str], lemmas: list[str], lemmas_to_refine: dict[str, str]) -> tuple[list[tuple[str, str]], list[dict]]:
    lemmas_str = '\n\n'.join(lemmas)
    definitions_str = '\n\n'.join(definitions)

    refined_lemmas = []
    for name, lemma in lemmas_to_refine.items():
        llm = LLM()
        prompt = REFINE_LEMMAS.format(theorem=theorem, proof_state=proof_state, definitions=definitions_str, lemmas=lemmas_str, lemma_to_refine=lemma)
        response = llm.query(prompt)[0]
        name, refined_lemma = parse_refine_lemmas(response, lemmas_to_refine)
        refined_lemmas.append((name, refined_lemma))

    return refined_lemmas, llm.conversation


def preprocess_lemma(proof_file: ProofFile, original_proof_term: ProofTerm, lemma: str) -> tuple[bool, ProofTerm, list[Step]]:
    start_index = proof_file.find_step_index(original_proof_term.ast.range) - 1
    complete = proof_file.parse_code('\n' + lemma)
    for ind, code in enumerate(complete):
        try:
            proof_file.add_step(start_index, code.text)
            proof_file.exec(1)
        except Exception as e:
            # error in the theorem statement, fail this
            print(e)
            for i_ in range(ind, 0, -1):
                proof_file.delete_step(start_index + i_)
            return False, None, []
        
        if proof_file.in_proof:
            initial_proof_steps = complete[ind+1:]
            break

    for open_thm in proof_file.open_proofs:
        if open_thm.step.short_text.strip() == code.short_text.strip():
            return True, open_thm, initial_proof_steps
    assert False


def validate_lemmas(proof_file: ProofFile, original_proof_term: ProofTerm, lemmas: list[tuple[str, str]]) -> tuple[dict[str, str], list[str], dict]:
    log = {}
    success_lemmas = {}
    failed_lemmas = []

    # abort the original proof
    proof_file.append_step(original_proof_term, '\nAbort.')

    for name, lemma in lemmas:
        stmt_valid, proof_term, initial_proof_steps = preprocess_lemma(proof_file, original_proof_term, lemma)
        if not stmt_valid:
            failed_lemmas.append(name)
            continue

        success, log_prove, partial_proof_str, goal_str, error_tactic, error_msg = prove_theorem(proof_file, proof_term, initial_proof_steps)
        log[name] = log_prove

        if success:
            success_lemmas[name] = proof_term.step.short_text.strip()
        else:
            changes_clear = [ProofPop() for _ in proof_term.steps]
            proof_file.change_proof(proof_term, changes_clear)
            failed_index = proof_file.find_step_index(proof_term.ast.range)
            proof_file.delete_step(failed_index)
            failed_lemmas.append(name)
            proof_term = None
        print('Refine lemma: ', name, success)
        assert not proof_file.in_proof

    proof_file.pop_step(original_proof_term)

    return success_lemmas, failed_lemmas, log


if __name__ == '__main__':
    pass
