from typing import Any
from collections import deque
import re

from agent_proof.repair_state import basic_repair, backtrack
from utils_hammer import *
from utils_coq import format_goal
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import Step, ProofTerm
from coqpyt.coq.exceptions import InvalidChangeException
from coqpyt.coq.changes import ProofPop

def clear_proof(proof_file: ProofFile, proof_term: ProofTerm):
    changes = [ProofPop() for _ in range(len(proof_term.steps))]
    proof_file.change_proof(proof_term, changes)


def get_final_proof(proof_term: ProofTerm):
    return [step.step.short_text for step in proof_term.steps]


def format_current_goal(proof_file: ProofFile):
    goals = proof_file.current_goals.goals.goals
    goal_str = format_goal(goals[0]) if goals else 'current goal completed'
    return goal_str


def prove(proof_file: ProofFile, proof_term: ProofTerm, steps: List[Step]) -> tuple[bool, dict[str, Any]]:
    exe_results = []
    steps = deque(steps)
    while steps:
        step = steps.popleft()
        text = step.text
        print('executing: ', text)
        if 'admit.' in text or 'Admitted.' in text:
            continue

        step_result = {'step': text, 'goal': format_current_goal(proof_file)}
        try:
            proof_file.append_step(proof_term, text)
            step_result['succ'] = True
            exe_results.append(step_result)
        except ResponseError as e:
            step_result['succ'] = False
            step_result['err_msg'] = str(e)
            exe_results.append(step_result)
            return False, {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), \
                            'stuck_state': step_result['goal'], 'error_tactic': step_result['step'], 'error_msg': ''}
        except InvalidChangeException as e:
            if not e.errors:
                continue
            error_msg = e.errors[-1].message
            step_result['succ'] = False
            step_result['err_msg'] = error_msg
            repair_success, steps, error_type = basic_repair(proof_file, proof_term, steps, step, error_msg)
            step_result['repair_type'] = error_type
            step_result['repair_succ'] = repair_success
            if repair_success:
                exe_results.append(step_result)
            else:
                hammer_succ, tactic = hammer(proof_file, proof_term)
                print("Hammering: ", hammer_succ)
                step_result['hammer_succ'] = hammer_succ
                if hammer_succ:
                    steps.appendleft(Step(f' {tactic}', tactic, None))
                    step_result['hammer_tactic'] = tactic
                    exe_results.append(step_result)
                else:
                    exe_results.append(step_result)
                    return False, {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), \
                                    'stuck_state': step_result['goal'], 'error_tactic': step_result['step'], 'error_msg': step_result['err_msg']}
        
        if proof_file.can_close_proof:
            try:
                proof_file.append_step(proof_term, "\nQed.")
                return True, {'success': True, 'results': exe_results, 'final_proof': get_final_proof(proof_term)}
            except Exception as e:
                log = {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), \
                        'stuck_state': format_current_goal(proof_file), 'error_tactic': '<incomplete proof>', 'error_msg': 'The proof is not completed'}
                clear_proof(proof_file, proof_term)
                return False, log
            
        
        # when no steps left and...
        cur_goals = proof_file.current_goals.goals
        if not steps:
            # ...the goal is just finished, there are other goals on stack
            if not cur_goals.goals and cur_goals.stack:
                assert cur_goals.bullet
                NEXT_BULLET = r'Focus next goal with bullet (.*?)\.'
                UNFOCUS_BRACE = r'Try unfocusing with "}"\.'
                matches_next_bullet = re.search(NEXT_BULLET, cur_goals.bullet)
                matches_unfocus_brace = re.search(UNFOCUS_BRACE, cur_goals.bullet)
                if matches_next_bullet:
                    groups = matches_next_bullet.groups()
                    bullet = groups[0]
                    # get the correct bullet, focus each goal on stack
                    for _ in range(len(cur_goals.stack)):
                        steps.appendleft(Step(f'\n{bullet}', bullet, None))
                elif matches_unfocus_brace:
                    steps.appendleft(Step('\n}', '}', None))
    
    if proof_file.can_close_proof:
        try:
            proof_file.append_step(proof_term, "\nQed.")
            return True, {'success': True, 'results': exe_results, 'final_proof': get_final_proof(proof_term)}
        except Exception as e:
            log = {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), \
                    'stuck_state': format_current_goal(proof_file), 'error_tactic': '<incomplete proof>', 'error_msg': 'The proof is not completed'}
            clear_proof(proof_file, proof_term)
            return False, log

    step_result = {'step': '$last_hammer$', 'goal': format_current_goal(proof_file)}
    hammer_succ, tactic = hammer(proof_file, proof_term)
    if hammer_succ:
        try:
            proof_file.append_step(proof_term, tactic)
            steps.appendleft(Step(f' {tactic}', tactic, None))
        except Exception as e:
            pass
    print("Last Hammering: ", hammer_succ)

    step_result['succ'] = hammer_succ
    step_result['hammer_succ'] = hammer_succ
    step_result['hammer_tactic'] = tactic
    exe_results.append(step_result)

    if proof_file.can_close_proof:
        try:
            proof_file.append_step(proof_term, "\nQed.")
            return True, {'success': True, 'results': exe_results, 'final_proof': get_final_proof(proof_term)}
        except Exception as e:
            log = {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), \
                    'stuck_state': format_current_goal(proof_file), 'error_tactic': 'incomplete proof', 'error_msg': 'The proof is not completed'}
            clear_proof(proof_file, proof_term)
            return False, log
    else:
        return False, {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), \
                        'stuck_state': format_current_goal(proof_file), 'error_tactic': 'incomplete proof', 'error_msg': 'The proof is not completed'}


def prove_hammer_first(proof_file: ProofFile, proof_term: ProofTerm, steps: List[Step]) -> Tuple[bool, Dict[str, Any]]:
    initial_goal = format_current_goal(proof_file)
    hammer_succ, tactic = hammer(proof_file, proof_term)
    if hammer_succ:
        try:
            proof_file.append_step(proof_term, f'\n{tactic}')
            proof_file.append_step(proof_term, f'\nQed.')
            return True, {'success': True, 'results': [{'step': f' {tactic}', 'goal': initial_goal, 'succ': True, 'hammer_succ': True, 'hammer_tactic': tactic}], 'final_proof': get_final_proof(proof_term), 'stuck_state': '', 'error_tactic': '', 'error_msg': ''}
        except Exception as e:
            clear_proof(proof_file, proof_term)
    return prove(proof_file, proof_term, steps)


def prove_backtrack(proof_file: ProofFile, proof_term: ProofTerm, steps: List[Step]) -> Tuple[bool, Dict[str, Any]]:
    exe_results = []
    steps = deque(steps)
    while steps:
        step = steps.popleft()
        # text = step.text.rstrip()
        text = step.text
        if text.strip() == 'Qed.':
            continue
        try:
            print('executing: ', text) 
            if step.short_text == 'admit.':
                continue
            step_result = {'step': text, 'goal': format_current_goal(proof_file)}
            proof_file.append_step(proof_term, text)
            step_result['succ'] = True
            exe_results.append(step_result)
        except InvalidChangeException as e:
            step_result['succ'] = False
            error_msg = e.errors[-1].message
            step_result['err_msg'] = error_msg
            repair_success, steps, error_type = basic_repair(proof_file, proof_term, steps, step, error_msg)
            step_result['repair_succ'] = repair_success
            step_result['repair_type'] = error_type
            exe_results.append(step_result)
            print('error: ', error_msg)
            if not repair_success:
                backtrack_success = backtrack(proof_file, proof_term, steps)
                step_result['succ'] = backtrack_success
                exe_results.append(step_result)
                if not backtrack_success:
                    return False, {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), 'stuck_state': format_current_goal(proof_file), 'error_tactic': 'incomplete proof', 'error_msg': 'The proof is not completed'}
        
        if proof_file.can_close_proof:
            try:
                proof_file.append_step(proof_term, "\nQed.")
                return True, {'success': True, 'results': exe_results, 'final_proof': get_final_proof(proof_term), 'stuck_state': '', 'error_tactic': '', 'error_msg': ''}
            except Exception as e:
                clear_proof(proof_file, proof_term)
                return False, {'success': False, 'results': exe_results, 'final_proof': get_final_proof(proof_term), 'stuck_state': format_current_goal(proof_file), 'error_tactic': 'incomplete proof', 'error_msg': 'The proof is not completed'}
        
        # when no steps left and...
        cur_goals = proof_file.current_goals.goals
        if not steps:
            # ...the goal is just finished, there are other goals on stack
            if not cur_goals.goals and cur_goals.stack:
                assert cur_goals.bullet
                NEXT_BULLET = r'Focus next goal with bullet (.*?)\.'
                UNFOCUS_BRACE = r'Try unfocusing with "}"\.'
                matches_next_bullet = re.search(NEXT_BULLET, cur_goals.bullet)
                matches_unfocus_brace = re.search(UNFOCUS_BRACE, cur_goals.bullet)
                if matches_next_bullet:
                    groups = matches_next_bullet.groups()
                    bullet = groups[0]
                    # get the correct bullet, focus each goal on stack
                    for _ in range(len(cur_goals.stack)):
                        steps.appendleft(Step(f'\n{bullet}', bullet, None))
                elif matches_unfocus_brace:
                    steps.appendleft(Step('\n}', '}', None))
    
    # backtrack_success = backtrack(proof_file, proof_term, steps)
    success = False
    if proof_file.can_close_proof:
        try:
            proof_file.append_step(proof_term, "\nQed.")
            success = True
        except Exception as e:
            clear_proof(proof_file, proof_term)
    else:
        success = False
    # exe_results.append({'step': '$backtrack$.', 'goal': format_current_goal(proof_file), 'succ': backtrack_success})

    return success, {'success': success, 'results': exe_results, 'final_proof': get_final_proof(proof_term), 'stuck_state': '', 'error_tactic': '', 'error_msg': ''}
