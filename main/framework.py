import os
from typing import Any
from coqpyt.coq.proof_file import ProofFile
from coqpyt.coq.structs import ProofTerm

from utils import json_load, json_dump
from utils_coq import get_ids_in_step_recursive
from agent_retrieval.agent import retrieve_similar_theorems, retrieve_current_lemmas, retrieve_current_terms_by_name
from agent_lemma.agent import lemma_discovery, lemma_refinement
from agent_proof.agent import prove_theorem_initial, prove_theorem_regenerate, prove_theorem_refine, prove_theorem_regenerate_new
from agent_retrieval.dependency_graph_simple_rango_file import Graph
from path import DATASET_NORMAL
from llm import LLM
from main.decision_maker import decision_initial_llm, decision_following_llm
from main.prompt import RETRIEVED_EXTRA_LEMMAS, NO_MORE_LEMMAS, NEW_LEMMA_DISCOVERY_REFINED, NO_NEW_LEMMAS, REGENERATE_FEEDBACK


def prove_llm_simpl_new(exp_name: str, proof_file: ProofFile, proof_term: ProofTerm, proj: str, commit: str, file_name: str, resume: str = '') -> tuple[bool, dict[str, Any]]:
    theorem_name = proof_file.context.get_names(proof_file.context.expr(proof_term.step))[0]
    theorem_str = proof_term.step.short_text
    definitions = get_ids_in_step_recursive(proof_file, proof_term)
    definitions = {name: term.step.short_text.strip() for name, term in definitions.items()}
    definitions_list = list(set(definitions.values()))

    print('start proving: ', theorem_name)
    log_file_path = os.path.join('./log', exp_name, proj, commit, file_name)
    log_path = os.path.join(log_file_path, theorem_name+'.json')

    datapoint_path = os.path.join(DATASET_NORMAL, proj, commit, 'datapoint')
    graph = Graph.from_proj_datapoint(datapoint_path, proj)

    log = []

    # generate initial proof and try to prove it
    resume_path = os.path.join('./log', resume, proj, commit, file_name, theorem_name+'.json')
    if resume and os.path.exists(resume_path):
        resume_log = json_load(resume_path)
        resume_log = resume_log[0]
        success = resume_log['success']
        partial_proof_initial = resume_log['partial_proof_initial']
        stuck_state_initial = resume_log['stuck_state']
        error_tactic_initial = resume_log['error_tactic']
        error_msg_initial = resume_log['error_msg']
    else:
        return False, []


    log.append({
        'iter': 0,
        'success': success,
        'partial_proof_initial': partial_proof_initial,
        'stuck_state_initial': stuck_state_initial,
        'error_tactic_initial': error_tactic_initial,
        'error_msg_initial': error_msg_initial,
    })

    if success:
        json_dump(log, log_path)
        return True, log
    
    # if failed, retrieve more context, including lemmas, ...
    lemmas_list, lemmas_dict = retrieve_current_lemmas(proof_file, proof_term)
    lemmas_list_top = lemmas_list[:11]
    lemmas_list_top_dict = {}
    for lemma in lemmas_list_top:
        for name, text in lemmas_dict.items():
            if text == lemma:
                lemmas_list_top_dict[name] = text
                break
    # ...similar proofs
    similar_proofs = retrieve_similar_theorems(theorem_str, theorem_name, definitions, file_name, graph, top=1)
    most_similar_theorem, similarity = similar_proofs[0]
    # ...definitions and lemmas in the most similar proof
    most_similar_theorem_definitions = graph.get_definitions_in_thm(most_similar_theorem)
    most_similar_theorem_definitions_list = [d.text.strip() for d in most_similar_theorem_definitions.values()]
    most_similar_theorem_lemmas = graph.get_lemmas_in_thm_recursive(most_similar_theorem)

    refined_lemmas = {}
    proposed_lemmas = {}

    stuck_state = stuck_state_initial
    partial_proof = partial_proof_initial
    error_tactic = error_tactic_initial
    error_msg = error_msg_initial
    # ask LLM what is the next action
    llm = LLM()
    for iter in range(1, 4):
        if iter == 1:
            decision, keywords = decision_initial_llm(theorem_str, partial_proof, stuck_state, definitions_list, lemmas_list_top, most_similar_theorem.get_complete(), llm)
        else:
            decision, keywords = decision_following_llm(llm)

        if decision == 'context_enrichment':
            # retrieve more context
            current_lemmas_list= [lemma.strip() for lemma in lemmas_list if any(keyword in lemma for keyword in keywords)]
            previous_lemmas = graph.get_accessible_terms(most_similar_theorem.file_path, keywords, lemma_only=True)
            previous_lemmas_list = [lemma.text.strip() for lemma in previous_lemmas.values()]
            previous_lemmas_list = [lemma for lemma in previous_lemmas_list if lemma not in current_lemmas_list]
            if len(current_lemmas_list) == 0 and len(previous_lemmas_list) == 0:
                prompt = NO_MORE_LEMMAS
            else:
                current_lemmas_str = '\n\n'.join(current_lemmas_list)
                previous_lemmas_str = '\n\n'.join(previous_lemmas_list)
                prompt = RETRIEVED_EXTRA_LEMMAS.format(lemmas_current=current_lemmas_str, lemmas_previous=previous_lemmas_str)
            llm.add_user_message(prompt)
            helpfer_lemmas = current_lemmas_list + list(proposed_lemmas.values()) + list(refined_lemmas.values())
            success, full_proof_regenerate, partial_proof_regenerate, stuck_state_regenerate, error_tactic_regenerate, error_msg_regenerate, conversation, log_gen, log_prove = prove_theorem_regenerate(proof_file, proof_term, stuck_state, theorem_str, partial_proof, definitions_list, helpfer_lemmas)
            # success, full_proof_regenerate, partial_proof_regenerate, stuck_state_regenerate, error_tactic_regenerate, error_msg_regenerate, conversation, log_gen, log_prove = prove_theorem_regenerate_new(regen_llm, proof_file, proof_term, stuck_state, theorem_str, partial_proof, error_tactic, error_msg, definitions_list, helpfer_lemmas)
            stuck_state = stuck_state_regenerate
            partial_proof = partial_proof_regenerate
            error_tactic = error_tactic_regenerate
            error_msg = error_msg_regenerate
            
            log.append({
                'iter': iter,
                'decision': 'context_retrieval',
                'success': success,
                'keywords': keywords,
                'current_lemmas': current_lemmas_list,
                'previous_lemmas': previous_lemmas_list,
                'conversation': llm.conversation,
                'all_refined_lemmas': refined_lemmas,
                'all_proposed_lemmas': proposed_lemmas,
                'log_gen': log_gen,
                'log_prove': log_prove,
            })
            if success:
                json_dump(log, log_path)
                return True, log

        elif decision == 'lemma_discovery':
            # propose new lemmas
            if keywords:
                # TODO
                to_refine_lemmas = {}
                for name in keywords:
                    thm = graph.get_thm_all_files(name)
                    if thm is not None:
                        to_refine_lemmas[name] = thm.get_complete().strip()
                non_exist_lemmas = {name: term.get_complete().strip() for name, term in most_similar_theorem_lemmas.items() if name not in lemmas_dict and name not in refined_lemmas}
                success_refine_lemmas, failed_refine_lemmas, log_lemma_refinement = lemma_refinement(proof_file, proof_term, theorem_str, most_similar_theorem_definitions_list, definitions_list, non_exist_lemmas)
            else:
                success_refine_lemmas = {}
                log_lemma_refinement = {}

            helper_lemmas = {name: lemmas_dict[name] for name in lemmas_dict}
            helper_lemmas.update(lemmas_list_top_dict)
            helper_lemmas.update(refined_lemmas)
            helper_lemmas.update(proposed_lemmas)
            success_propose_lemmas, failed_propose_lemmas, log_lemma_discovery = lemma_discovery(proof_file, proof_term, helper_lemmas)

            refined_lemmas.update(success_refine_lemmas)
            proposed_lemmas.update(success_propose_lemmas)

            if len(success_refine_lemmas) + len(success_propose_lemmas) == 0:
                prompt = NO_NEW_LEMMAS
            else:
                refined_lemmas_str = '\n\n'.join(success_refine_lemmas.values())
                proposed_lemmas_str = '\n\n'.join(success_propose_lemmas.values())
                prompt = NEW_LEMMA_DISCOVERY_REFINED.format(refined_lemmas=refined_lemmas_str, new_lemmas=proposed_lemmas_str)
            llm.add_user_message(prompt)
            helpfer_lemmas = lemmas_list_top + list(proposed_lemmas.values()) + list(refined_lemmas.values())
            success, full_proof_regenerate, partial_proof_regenerate, stuck_state_regenerate, error_tactic_regenerate, error_msg_regenerate, conversation, log_gen, log_prove = prove_theorem_regenerate(proof_file, proof_term, stuck_state, theorem_str, partial_proof, definitions_list, helpfer_lemmas)
                # success, full_proof_regenerate, partial_proof_regenerate, stuck_state_regenerate, error_tactic_regenerate, error_msg_regenerate, conversation, log_gen, log_prove = prove_theorem_regenerate_new(regen_llm, proof_file, proof_term, stuck_state, theorem_str, partial_proof, error_tactic, error_msg, definitions_list, helpfer_lemmas)
            stuck_state = stuck_state_regenerate
            partial_proof = partial_proof_regenerate
            error_tactic = error_tactic_regenerate
            error_msg = error_msg_regenerate

            log.append({
                'iter': iter,
                'decision': 'lemma_discovery',
                'success': success,
                'refined_lemmas': success_refine_lemmas,
                'proposed_lemmas': success_propose_lemmas,
                'log_gen': log_gen,
                'log_prove': log_prove,
            })
            if success:
                json_dump(log, log_path)
                return True, log

        elif decision == 'regenerate':
            # regenerate the proof
            helper_lemmas = {name: lemmas_dict[name] for name in lemmas_dict}
            helper_lemmas.update(lemmas_list_top_dict)
            helper_lemmas.update(refined_lemmas)
            helper_lemmas.update(proposed_lemmas)
            helper_lemmas_list = [item.text.strip() for item in helper_lemmas.values()]
            # generate a new proof
            success, full_proof_regenerate, partial_proof_regenerate, stuck_state_regenerate, error_tactic_regenerate, error_msg_regenerate, conversation, log_gen, log_prove = prove_theorem_regenerate(proof_file, proof_term, stuck_state, error_tactic, error_msg, theorem_str, partial_proof, definitions_list, helper_lemmas_list, most_similar_theorem.get_complete())
            stuck_state = stuck_state_regenerate
            partial_proof = partial_proof_regenerate
            error_tactic = error_tactic_regenerate
            error_msg = error_msg_regenerate

            log.append({
                'iter': iter,
                'decision': 'regenerate',
                'success': success,
                'log_gen': log_gen, 
                'log_prove': log_prove,
            })

            if success:
                json_dump(log, log_path)
                return True, log
            else:
                prompt = REGENERATE_FEEDBACK.format(generated_proof=full_proof_regenerate, partial_proof=partial_proof_regenerate, proof_state=stuck_state_regenerate, error_tactic=error_tactic_regenerate, error_msg=error_msg_regenerate)
                llm.add_user_message(prompt)
    json_dump(log, log_path)
    return False, log
