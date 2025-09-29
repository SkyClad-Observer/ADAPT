from llm import LLM
from main.prompt import DECISIONS_INSTRUCTION, DECISION_MAKING_INITIAL
from utils_coq import extract_code_blocks


def parse_kws(response: str):
    semicolon_first = response.find(';')
    kws = response[semicolon_first + 1:].strip()

    if not kws.startswith('[') or not kws.endswith(']'):
        return []
    kws = kws[1:-1].strip()
    if not kws:
        return []
    kws = kws.split(',')
    kws = [kw.strip() for kw in kws if kw.strip()]
    return kws
    

### Decision Making ###
def parse_decision_response(response: str) -> tuple[str, list[str]]:
    response = response.strip()
    if not response.startswith('```') or not response.endswith('```'):
        return None, []
    
    response = response[3:-3].strip()
    assert response.startswith('Context Enrichment') or response.startswith('Lemma Discovery') or response.startswith('Regenerate'), f'Invalid response: {response}'
    
    if response.startswith('Context Enrichment'):
        action = 'context_enrichment'
        keywords = parse_kws(response)
        return action, {'keywords': keywords}
    elif response.startswith('Lemma Discovery'):
        action = 'lemma_discovery'
        response = response[len('Lemma Discovery'):].strip()
        keywords = parse_kws(response)
        return action, keywords
    elif response.startswith('Regenerate'):
        action = 'regenerate'
        return action, []
    assert False, f'Invalid response: {response}'
    

def decision_initial_llm(theorem: str, partial_proof: str, proof_state: str, definitions: list[str], lemmas: list[str], similar_theorem: str, llm: LLM) -> tuple[str, list[str]]:
    definitions_str = '\n\n'.join(definitions)
    lemmas_str = '\n\n'.join(lemmas)
    prompt = DECISION_MAKING_INITIAL.format(theorem=theorem, partial_proof=partial_proof, proof_state=proof_state, definitions=definitions_str, lemmas=lemmas_str, similar_theorem=similar_theorem)
    response = llm.query(prompt)[0]
    action, kws = parse_decision_response(response)
    return action, kws


def decision_following_llm(llm: LLM) -> tuple[str, list[str]]:
    prompt = DECISIONS_INSTRUCTION.strip()
    response = llm.query(prompt)[0]
    action, kws = parse_decision_response(response)
    return action, kws


if __name__ == '__main__':
    pass
