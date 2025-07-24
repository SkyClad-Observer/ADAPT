from typing import List, Dict, Tuple, Deque

from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.base_file import CoqFile
from coqpyt.coq.context import FileContext
from coqpyt.coq.structs import Term, Step, ProofTerm
from coqpyt.coq.lsp.structs import Goal, Hyp
from coqpyt.coq.exceptions import InvalidChangeException

from ..utils_hammer import hammer, hammer_tactic
from ..utils_coq import *


UNFINISHED_BULLET = r'Wrong bullet (.*?): Current bullet (.*?) is not finished'
WRONG_BULLET = r'Wrong bullet (.*?): Expecting (.*?)\.'
WRONG_BULLET_UNFOUCS = r'Wrong bullet (.*?): Try unfocusing with "(.*?)"\.'
NO_MORE_GOALS = r'Wrong bullet (.*?): No more goals' # todo
NO_MORE_SUBGOALS = r'Wrong bullet (.*?): No more subgoals'
FAILED_BULLET = r'Proof_bullet.Strict.FailedBullet'
WRONG_UNFOCUS = r'This proof is focused, but cannot be unfocused this way' # }. todo
NEXT_GOAL = r'No such goal. Focus next goal with bullet (.*?)\.'
NO_GOAL = r'No such goal'


def get_bullets(proof_file: ProofFile, proof_term: ProofTerm) -> List[str]:
    result = []
    steps = proof_term.steps
    for step in steps:
        text = step.step.short_text.strip()
        if is_bullet(text):
            if text in result:
                result = result[:result.index(text) + 1]
            else:
                result.append(text)
    return result


hammer_tactics = ['srun', 'sinit', 'sauto', 'sintuition', 'ssimpl', 'qsimpl', 'scrush', \
                  'fcrush', 'ecrush', 'sblast', 'qblast', 'scongruence', 'sfirstorder', 'strivial']

def is_hammer_tactic(tactic: str) -> bool:
    tactic = tactic.strip()
    for ht in hammer_tactics:
        if tactic.startswith(ht + ' ') or tactic == ht + '.':
            return True
    return False

def backtrack(proof_file: ProofFile, proof_term: ProofTerm, steps: Deque[Step]) -> bool: 
    hammer_times = 0
    print('start backtrack')
    while True:
        succ, replace = hammer(proof_file, proof_term)
        print('hammering: ', hammer_times, succ)
        hammer_times += 1
        if succ:
            proof_file.append_step(proof_term, replace)
            # print(replace)
            # print(proof_file.current_goals)
            if not proof_file.current_goals.goals.goals:
                return True
            else:
                proof_file.pop_step(proof_term)
        # else:
        if not proof_term.steps or proof_term.steps[-1].step.short_text == 'Proof.':
            return False
        
        if is_bullet(proof_term.steps[-1].step.short_text):
            bullets = get_bullets(proof_file, proof_term)
            target_bullet = bullets[-1]
            # remove all (already executed) steps with the same bullet 
            for i, step in enumerate(proof_term.steps):
                if step.step.short_text == target_bullet:
                    while i < len(proof_term.steps):
                        proof_file.pop_step(proof_term)

            # remove steps with the same bullet in the following (unexecuted) steps
            # if only one layer, remove all
            # step1. induction.
            # - step2. error_step (backtrack here)
            # - ... (all should be removed)
            if len(bullets) == 1:
                while steps:
                    steps.popleft()
            # multiple layers
            # step1. induction.
            # - step2. induction2 
            #   + error_step (backtrack here)
            #   + step3. ... (until the bullet of last layer, should be removed)
            # - step4. ...
            else:
                last_bullet = bullets[-2]
                while steps and not steps[0].short_text == last_bullet:
                    steps.popleft()

        proof_file.pop_step(proof_term)
        while proof_term.steps and is_hammer_tactic(proof_term.steps[-1].step.short_text):
            proof_file.pop_step(proof_term)
        if proof_term.steps and proof_term.steps[-1].step.short_text == '}':
            proof_file.pop_step(proof_term)
            while proof_term.steps and proof_term.steps[-1].step.short_text != '{':
                proof_file.pop_step(proof_term)
            proof_file.pop_step(proof_term)


# TODO: verify this
def get_next_bullet(proof_file: ProofFile, proof_term: ProofTerm, start: str = '') -> str:
    current_bullets = get_bullets(proof_file, proof_term)
    if not start:
        start = current_bullets[-1] if current_bullets else '-'
    
    succ, error = execute_once(proof_file, proof_term, '\n' + start)
    if succ:
        return start
    
    error_message = error.diagnostics[-1].message
    matches = re.search(WRONG_BULLET, error_message)
    if matches:
        _, res = matches.groups()
        return res
    matches = re.search(UNFINISHED_BULLET, error_message)
    if matches:
        _, cur = matches.groups()
        nx = next_bullet(cur)
        while nx in current_bullets:
            nx = next_bullet(nx)
        return get_next_bullet(proof_file, proof_term, nx)
    matches = re.search(WRONG_BULLET_UNFOUCS, error_message)
    if matches:
        raise 'next_indicator error'
    matches = re.search(NO_MORE_GOALS, error_message)
    if matches:
        return None
    matches = re.search(NO_MORE_SUBGOALS, error_message)
    if matches:
        return None
    raise 'next_indicator error'


###### REPAIR INTROS ######

USED_VAR = r'(.*?) is ((already used)|(used twice))'
NO_PRODUCT = r'No product even after head-reduction' # intros. todo

# TODO: fix this
def used_var(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    used_name = groups[0].strip()
    return steps


def no_product(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    return steps

errors_intros = {
    'used_var': (USED_VAR, used_var),
    'no_product': (NO_PRODUCT, no_product), # 2
}

def repair_intros(proof_file: ProofFile, proof_term: ProofTerm, steps: Deque[Step], error_step: Step) -> Tuple[bool, List[str]]:
    pass

###### REPAIR BULLETS ######


def unfinished_bullet(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    steps.appendleft(Step('\n' + groups[0], groups[0], None))
    return steps
    

def wrong_bullet(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    _, bullet = groups
    steps.appendleft(Step('\n' + bullet, bullet, None))
    return steps


def wrong_bullet_unfocus(msg, groups, state, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    _, unfocus = groups
    new_step = Step('\n' + unfocus, unfocus, None)
    steps.appendleft(new_step)
    return steps


def no_more_goals(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    assert proof_file.can_close_proof
    return Deque()


def no_more_subgoals(msg, groups, state, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    return Deque()


# TODO: fix this
def failed_bullet(msg, groups, state, steps: Deque[Step], error_step: Step):
    # tactics.appendleft('shelve.')
    return ['shelve.']


def next_goal(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    bullet = groups[0]
    while steps and not steps[0].short_text == bullet:
        steps.popleft()
    return steps


def no_goal(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    cur_goals = proof_file.current_goals.goals
    
    # can close?
    if proof_file.can_close_proof:
        return Deque()
    
    # can't close, but no cur goal, have unfocused goals
    # assert not cur_goals.goals

    if not cur_goals.bullet:
        # should have braces, or the message must contain the bullet info
        # assert any([s.step.short_text.endswith('{') for s in proof_term.steps])
        if any([s.step.short_text.endswith('{') for s in proof_term.steps]):
            steps.appendleft(Step('\n}', '}', None))
        else:
            return steps
    else:
        return steps
        
    return Deque()


errors_bullet = {
    'unfinished_bullet': (UNFINISHED_BULLET, unfinished_bullet),
    'wrong_bullet': (WRONG_BULLET, wrong_bullet),
    'no_more_goals': (NO_MORE_GOALS, no_more_goals),
    'no_more_subgoals': (NO_MORE_SUBGOALS, no_more_subgoals),
    # 'failed_bullet': (FAILED_BULLET, failed_bullet),
    'next_goal': (NEXT_GOAL, next_goal),
    'no_goal': (NO_GOAL, no_goal),
}


def qsimpl_premise(proof_file: ProofFile, proof_term: ProofTerm, groups, steps: Deque[Step], error_step: Step) -> Deque[Step]:
    definitions = get_ids_in_step(proof_file, error_step)
    definitions = [name for name, _ in definitions.items() if name in proof_file.context.terms]
    if not definitions:
        tactic = '\nqsimpl.'
    else:
        definitions_str = ', '.join(definitions)
        tactic = f'\nqsimpl use: {definitions_str}.'
    steps.appendleft(Step(tactic, tactic, None))
    return steps


def basic_repair(proof_file: ProofFile, proof_term: ProofTerm, steps: Deque[Step], error_step: Step, error_message: str) -> Tuple[bool, Deque[str], str]:
    errors_all = {**errors_intros, **errors_bullet}
    for error_type, (pattern, repair) in errors_all.items():
        matches = re.search(pattern, error_message)
        if matches:
            if error_type == 'no_goal' and re.search(NEXT_GOAL, error_message):
                continue
            
            new_steps = repair(proof_file, proof_term, matches.groups(), steps, error_step)
            return error_type != 'unfinished_bullet', new_steps, error_type
        
    matches_unfinished = re.search(UNFINISHED_BULLET, error_message)
    if matches_unfinished:
        return False, steps, 'unfinished_bullet'
    
    # TODO: should check error tactic instead.
    # if 'rewrite' in error_step.short_text or 'apply' in error_step.short_text:
    #     return True, qsimpl_premise(proof_file, proof_term, None, steps, error_step), 'qsimpl_premise'
    return False, steps, None
    

# def backtrack(proof_file: ProofFile, proof_term: ProofTerm) -> Tuple[bool, List[str]]:
    