from typing import List, Dict, Tuple
from utils_coq import normalize_spaces
from coqpyt.coq.structs import Term, Step, ProofTerm
from coqpyt.coq.lsp.structs import Goal, Hyp, GoalConfig, GoalAnswer
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.exceptions import InvalidChangeException
from coqpyt.lsp.structs import ResponseError


def eq_hyp(hyp_1: Hyp, hyp_2: Hyp) -> bool:
    if normalize_spaces(hyp_1.ty) != normalize_spaces(hyp_2.ty):
        return False
    if len(hyp_1.names) != len(hyp_2.names):
        return False
    names_1 = set(hyp_1.names)
    names_2 = set(hyp_2.names)
    return names_1 == names_2


def eq_goal(goal_1: Goal, goal_2: Goal) -> bool: 
    if normalize_spaces(goal_1.ty) != normalize_spaces(goal_2.ty):
        return False
    if len(goal_1.hyps) != len(goal_2.hyps):
        return False
    
    hyps_1 = [h for h in goal_1.hyps]
    hyps_2 = [h for h in goal_2.hyps]

    remove = []
    for i in range(len(hyps_1)):
        found = False
        for j in range(len(hyps_2)):
            if eq_hyp(hyps_1[i], hyps_2[j]):
                hyps_2.pop(j)
                remove.append(i)
                found = True
                break
        if not found:
            return False
    for r in remove:
        hyps_1.pop(r)
    
    if len(hyps_1) > 0:
        return False
    return True

# TODO: sometimes, qimpl use: lemma just adds the lemma to the hyps. This does not make progress.
def progress(old_state: GoalAnswer, new_state: GoalAnswer) -> bool:
    old_goals = old_state.goals.goals
    new_goals = new_state.goals.goals

    if len(old_goals) != len(new_goals):
        return True
    if eq_goal(old_goals[0], new_goals[0]):
        return False
    return True


def automation(proof_file: ProofFile, proof_term: ProofTerm, tactic: str) -> Tuple[bool, str]:
    try:
        proof_file.append_step(proof_term, f'\n{tactic}')
        step = proof_term.steps[-1]
        message = step.diagnostics[-1].message
        return True, message
    except InvalidChangeException as e:
        error_messages = e.errors[-1].message
        return False, error_messages
    except ResponseError as e:
        print("ResponseError: ", e)
        print("Last step: ", proof_term.steps[-1].text)
        return False, str(e)


def hammer_tactic(proof_file: ProofFile, proof_term: ProofTerm, tactic: str) -> Tuple[bool, str]:
    tactic = tactic.strip()
    assert tactic.startswith('qsimpl') or tactic.startswith('sauto') or tactic.startswith('ssimpl'), tactic
    old_state = proof_file.current_goals
    sucess, message = automation(proof_file, proof_term, f' {tactic}')
    if not sucess:
        return False, message
    
    new_state = proof_file.current_goals
    if progress(old_state, new_state):
        return True, ''
    else:
        proof_file.pop_step(proof_term)
        return False, 'No progress'


def hammer(proof_file: ProofFile, proof_term: ProofTerm) -> Tuple[bool, str]:
    tactic = 'hammer.'

    # print('start hammer')
    sucess, message = automation(proof_file, proof_term, tactic)
    # print('Hammer res: ', sucess, message)
    if not sucess:
        return False, message
    proof_file.pop_step(proof_term)
    prefix = 'Replace the hammer tactic with:'
    assert message.startswith(prefix), message
    replace = message[len(prefix)+1:].strip()
    if not replace.endswith('.'):
        replace += '.'

    # "srun eauto" causes error, use "srun best" instead
    if replace.startswith('srun eauto '):
        replace = replace.replace('srun eauto ', 'best ')
    return True, '\n' + replace
