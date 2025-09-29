import re
import random
import os
from utils import extract_code_blocks
from typing import List, Dict, Tuple
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.base_file import CoqFile
from coqpyt.coq.context import FileContext
from coqpyt.coq.structs import Term, Step, ProofTerm
from coqpyt.coq.lsp.structs import Goal, Hyp
from coqpyt.coq.exceptions import InvalidChangeException
from datetime import datetime


def parse_code(code: str) -> list[Step]:
    timestamp = str(datetime.now().timestamp()).replace('.', '')
    file_name = f'__parse__{timestamp}.v'
    code = '\n' + code.strip()
    with open(file_name, 'w') as f:
        f.write(code)
    with CoqFile(file_name) as coq_file:
        steps = coq_file.steps
    os.remove(file_name)
    return steps


def parse_response_proof(response: str) -> List[Step]:
    blocks = extract_code_blocks(response.strip())
    if len(blocks) == 0:
        return []
    code = blocks[-1].strip()
    code = remove_comments(code)
    steps = parse_code(code) # coq_file.parse_code('\n\n' + code)
    for i in range(len(steps)):
        if steps[i].short_text == 'Proof.':
            return steps[i+1:]
    return steps


def format_goal(goal: Goal) -> str:
    hyps, ty = goal.hyps, goal.ty
    result = "(* Hypotheses: *)\n{hypotheses}\n\n(* Goal: *)\n{goal}"
    hypotheses = ""
    for hyp in hyps:
        names = ", ".join(hyp.names)
        hypotheses += f"{names} : {hyp.ty}\n"
    return result.format(hypotheses=hypotheses, goal=ty)


def get_theorem_name(text: str) -> str:
    NAME_PATTERN = re.compile(r"\S+\s+(\S+?)[\[\]\{\}\(\):=,\s]")
    name_match = NAME_PATTERN.search(text)
    if name_match is not None:
        (name,) = name_match.groups()
        return name
    

def get_ids_from_sentence(text) -> list[str]:
    ID_FORM = re.compile(r"[^\[\]\{\}\(\):=,\s]+")
    sentence_ids = re.findall(ID_FORM, text)
    return sentence_ids


def is_bullet(step: str) -> bool:
    return all(char == '-' for char in step) \
        or all(char == '+' for char in step) \
        or all(char == '*' for char in step)


def next_bullet(bullet: str):
    if bullet == '':
        return '-'
    if not is_bullet(bullet):
        return ''
    else:
        indi = bullet[0]
        length = len(bullet)
        if indi == '-':
            return '+'*length
        elif indi == '+':
            return '*'*length
        else:
            return '-'*(length+1)


def _get_all_ids(expr: List) -> List[str]:
    stack, res = expr[:0:-1], []
    while len(stack) > 0:
        el = stack.pop()
        if isinstance(el, dict):
            for v in reversed(el.values()):
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(el, list):
            for v in reversed(el):
                if isinstance(v, (dict, list)):
                    stack.append(v)
        if FileContext.is_id(el):
            res.append(FileContext.get_id(el))
    return res


def in_std_lib(term: Term | str) -> bool:
    if isinstance(term, Term):
        file_path = term.file_path
    else:
        file_path = term
    if 'user-contrib' in file_path:
        return False
    if '/lib/coq/' in file_path:
        return True
    return False


def is_within_proj(term: Term, proj: str) -> bool:
    file_path = term.file_path
    if proj in file_path:
        return True
    return False


def get_ids_in_step(proof_file: ProofFile, code: Term | Step | str, remove_std: bool = True) -> Dict[str, Term]:
    if isinstance(code, str):
        names = get_ids_from_sentence(code)
    else:
        if isinstance(code, Term):
            code = code.step
        expr = proof_file.context.expr(code)
        names = set(_get_all_ids(expr))
    results = {}
    for name in names:
        term = proof_file.context.get_term(name)
        if not term:
            continue
        if remove_std and in_std_lib(term):
            continue
        results[name] = term
    return results


def get_ids_in_step_recursive(proof_file: ProofFile, code: Term | Step | str, remove_std: bool = True) -> Dict[str, Term]:
    results = get_ids_in_step(proof_file, code, remove_std)
    checked = set()
    while True:
        original_size = len(results)
        new_results = {}
        for name, term in results.items():
            if name in checked:
                continue
            res = get_ids_in_step(proof_file, term, remove_std)
            new_results.update(res)
            checked.add(name)
        results.update(new_results)
        if len(results) == original_size:
            break
    return results


def execute_once(proof_file: ProofFile, proof_term: ProofTerm, step: str) -> Tuple[bool, InvalidChangeException | None]:
    try:
        result = proof_file.append_step(proof_term, step)
        error = None
    except InvalidChangeException as e:
        result = False
        error = e
    finally:
        proof_file.pop_step(proof_term)
        return result, error


def remove_comments(code: str) -> str:
    result = []
    i = 0
    while i < len(code):
        # Check for the start of a comment
        if code[i:i+2] == "(*":
            # Move the index forward until the end of the comment
            i += 2
            while i < len(code) and code[i:i+2] != "*)":
                i += 1
            i += 2  # Skip the closing "*)"
        else:
            result.append(code[i])
            i += 1
    return ''.join(result).strip()


def is_import(step: str) -> bool:
    step = step.strip()
    if step.startswith('Import ') or step.startswith('Export '):
        return True
    if step.startswith('Require Import ') or step.startswith('Require Export '):
        return True
    if step.startswith('From ') and ' Require ' in step:
        return True
    return False


# def parse_code(code: str) -> List[Step]:
#     code = code.replace('rewrite -> ', 'rewrite ')
#     with open('temp.v', 'w') as f:
#         f.write(code)
#     with CoqFile('temp.v') as coq_file:
#         steps = coq_file.steps
#     return steps


def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s, flags=re.DOTALL)


if __name__ == "__main__":
    code = """
    (* Now we need to prove that list_order il_0 u_0 u_1 = false if list_member il_1 u_1 = false *)
    (*asdasd*)induction il_0 as [| h t IH]. (*asdasd*)
    """
    print(remove_comments(code))

