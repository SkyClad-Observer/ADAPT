from typing import Any
import os
import json
import re
from coqpyt.coq.structs import ProofTerm, ProofStep, Term
from agent_retrieval.tactics import all_tactics, keywords

types = ['LEMMA', 'THEOREM', 'COROLLARY']

def in_std_lib(file_path: str) -> bool:
    if 'user-contrib' in file_path:
        return False
    if '/lib/coq/' in file_path:
        return True
    return False


def get_theorem_name(text: str) -> str:
    NAME_PATTERN = re.compile(r"\S+\s+(\S+?)[\[\]\{\}\(\):=,\s]")
    name_match = NAME_PATTERN.search(text)
    if name_match is not None:
        (name,) = name_match.groups()
        return name
    

def get_ids_from_sentence(text) -> list[str]:
    ID_FORM = re.compile(r"[^\[\]\{\}\(\);:=,\s]+")
    sentence_ids = re.findall(ID_FORM, text)
    sentence_ids_sanitized = []
    for id_ in sentence_ids:
        if id_ in all_tactics or id_ in keywords:
            continue
        if id_.endswith('.'):
            id_ = id_[:-1].strip()
        sentence_ids_sanitized.append(id_)
    return sentence_ids_sanitized


def get_rel_path(file_path: str, proj: str) -> str:
    proj_index = file_path.find(proj)
    if proj_index != -1:
        file_path = file_path[proj_index + len(proj) + 1:]
    return file_path


class CtxTerm:
    def __init__(self, type: str, text: str, file_path: str, module: str, line: int):
        if '.' in type:
            type = type.split('.')[-1]
        self.type = type
        self.text = text
        self.file_path = file_path
        self.module = module
        self.line = line
        # TODO: Definition, Fixpoint, Inductive, .etc
        if type in ['LEMMA', 'THEOREM', 'COROLLARY', 'DEFINITION', 'FIXPOINT', 'COFIXPOINT', 'INDUCTIVE', 'COINDUCTIVE']:
            self.name = get_theorem_name(text)
        else:
            self.name = None
    
    def is_definition(self) -> bool:
        return self.type in ['DEFINITION', 'FIXPOINT', 'COFIXPOINT', 'INDUCTIVE', 'COINDUCTIVE']
    
    def is_lemma(self) -> bool:
        return self.type in ['LEMMA', 'THEOREM', 'COROLLARY']
    
    @staticmethod
    def from_json(data: dict[str, Any]):
        type, text, file_path, module = data['type'], data['text'], data['file_path'], data['module']
        line = data['line']
        file_path = get_rel_path(file_path, Graph.proj)
        return CtxTerm(type, text, file_path, module, line)
    
    @staticmethod
    def from_term(term: Term):
        return CtxTerm(term.type.name, term.step.short_text, term.file_path, term.module, -1)


class Context:
    def __init__(self, terms: set[CtxTerm]):
        self.terms = terms
        self.name_to_term = {term.name: term for term in terms if term.name is not None}

    def get_term_by_name(self, name: str) -> CtxTerm:
        if name in self.name_to_term:
            return self.name_to_term[name]
        else:
            return None
        
    @staticmethod
    def from_json(data: list[str]):
        terms = set()
        lines = [json.loads(line) for line in data]
        for line in lines[1:]:
            term = CtxTerm.from_json(line)
            terms.add(term)
        return Context(terms)


class MyStep:
    def __init__(self, text: str, goals: list[str]):
        self.text = text
        self.goals = goals

    def get_ids_in_text(self) -> list[str]:
        return get_ids_from_sentence(self.text)
    
    @staticmethod
    def from_step(step: ProofStep):
        text = step.step.short_text
        goals = step.goals.goals
        if goals is None:
            return MyStep(text, goals)
        
        goals = goals.goals
        goals_strs = [repr(goal) for goal in goals]
        return MyStep(text, goals_strs)
    

    @staticmethod
    def from_json(data: dict[str, Any]):
        text, goals = data['step']['text'], data['goals']
        return MyStep(text, goals)


class Thm:
    def __init__(self, name: str, text: str, steps: list[MyStep], file_path: str, line: int):
        self.name = name
        self.text = text
        self.steps = steps
        self.file_path = file_path
        self.line = line
    
    def __hash__(self):
        return f'{self.file_path}/{self.text}'.__hash__()
    
    def __eq__(self, value):
        return self.file_path == value.file_path and self.text == value.text
    
    def get_full_name(self):
        return f"{self.file_path}/{self.name}"
    
    def get_proof(self) -> str:
        return ''.join([step.text for step in self.steps])
    
    def get_complete(self) -> str:
        return f'{self.text}{self.get_proof()}'
    
    def get_ids_text(self) -> set[str]:
        ids_ = get_ids_from_sentence(self.text)
        ids_ = {id_ for id_ in ids_ if id_ != self.name}
        return ids_

    def get_ids_proof(self) -> set[str]:
        ids = set()
        for step in self.steps:
            ids.update(step.get_ids_in_text())
        ids = {id_ for id_ in ids if id_ != self.name}
        return ids
    
    def get_ids(self) -> set[str]:
        ids = self.get_ids_text()
        ids.update(self.get_ids_proof())
        return ids
    
    def to_ctx_term(self) -> CtxTerm:
        return CtxTerm('THEOREM', self.text, self.file_path, None, -1)
    

    @staticmethod
    def from_proof_term(proof_term: ProofTerm):
        steps = [MyStep.from_step(step) for step in proof_term.steps]
        text = proof_term.step.short_text
        file_path = proof_term.file_path
        name = get_theorem_name(text)
        return Thm(name, text, steps, file_path, -1) 
    

    @staticmethod
    def from_json(data: dict[str, Any]):
        theorem, steps = data['theorem'], data['steps']
        text, file_path, line = theorem['text'], theorem['file_path'], theorem['line']
        file_path = get_rel_path(file_path, Graph.proj)
        name = get_theorem_name(text)
        steps = [MyStep.from_json(step) for step in steps]
        return Thm(name, text, steps, file_path, line)
    

class GraphFile:
    def __init__(self, file_path: str, context: Context, all_theorems_list: list[Thm], metadata: dict[str, Any]):
        self.context = context
        self.all_theorems_list = all_theorems_list
        self.file_path = file_path
        self.metadata = metadata


    def add_proof(self, proof_term: ProofTerm):
        proof = Thm.from_proof_term(proof_term)
        self.all_theorems_list.append(proof)


    def get_accessible_thms(self, thm: Thm, remove_std: bool = True) -> set[CtxTerm]:
        res = []
        for term in self.context.terms:
            if not term.is_lemma():
                continue
            if remove_std and in_std_lib(term.file_path):
                continue
            res.append(term)

        for thm_ in self.all_theorems_list:
            if thm.name == thm_.name:
                return res
            res.append(thm_)
        return res
    

    def get_thm(self, name: str) -> Thm:
        for thm in self.all_theorems_list:
            if thm.name == name:
                return thm
        return None
    

    def get_terms_in_text(self, text: str, remove_std: bool = True) -> dict[str, CtxTerm]:
        res = {}
        ids_all = get_ids_from_sentence(text)
        for id_ in ids_all:
            term = self.context.get_term_by_name(id_)
            if term is not None:
                if remove_std and in_std_lib(term.file_path):
                    continue
                res[id_] = term
        return res
    

    def get_terms_in_text_recursive(self, text: str, remove_std: bool = True) -> dict[str, CtxTerm]:
        result = self.get_terms_in_text(text, remove_std)
        checked = set()
        while True:
            original_size = len(result)
            new_results = {}
            for name, term in result.items():
                if name in checked:
                    continue
                res = self.get_terms_in_text(term.text, remove_std)
                new_results.update(res)
                checked.add(name)
            result.update(new_results)
            if len(result) == original_size:
                break
        return result
    

    def get_definitions_in_thm(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        terms = self.get_terms_in_text_recursive(thm.text, remove_std)
        terms = {k: v for k, v in terms.items() if k != thm.name}
        return terms
    

    def get_lemmas_in_thm(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        res = {}
        ids_all = thm.get_ids()
        acc_thms = self.get_accessible_thms(thm, remove_std)
        for id_ in ids_all:
            for acc_thm in acc_thms:
                if id_ == acc_thm.name:
                    res[id_] = acc_thm
        return res
    

    def get_lemmas_in_thm_recursive(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        """
        Get all lemmas used in a theorem recursively within this file.
        If theorem A uses lemma B and lemma B uses lemma C, then
        the result will include both B and C.
        
        Args:
            thm: The theorem to analyze
            remove_std: Whether to remove standard library lemmas
            
        Returns:
            Dictionary mapping lemma names to their CtxTerm representations
        """
        result = self.get_lemmas_in_thm(thm, remove_std)
        checked = set()
        to_check = list(result.values())
        
        while to_check:
            term = to_check.pop(0)
            if term.name in checked:
                continue
            
            # Get the theorem object for this lemma
            lemma_thm = self.get_thm(term.name)
            if lemma_thm is None:
                # This might be from a different file or a built-in lemma
                checked.add(term.name)
                continue
                
            # Get lemmas used in this lemma
            lemmas_in_lemma = self.get_lemmas_in_thm(lemma_thm, remove_std)
            
            # Add new lemmas to the result
            for name, new_term in lemmas_in_lemma.items():
                if name not in checked and name not in result:
                    result[name] = new_term
                    to_check.append(new_term)
            
            checked.add(term.name)
            
        return result
    
    def get_definitions_and_lemmas_in_thm(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        terms = self.get_definitions_in_thm(thm, remove_std)
        terms.update(self.get_lemmas_in_thm(thm, remove_std))
        return terms
    

    @staticmethod
    def from_one_datapoint(datapoint_file_path: str):
        data = json.load(open(datapoint_file_path))
        file_context, proofs = data['file_context'], data['proofs']
        file_path = json.loads(file_context[0])['file']
        file_path = get_rel_path(file_path, Graph.proj)

        context = Context.from_json(file_context)
        theorems_list = []
        for proof in proofs:
            type_ = proof['theorem']['type']
            type_ = type_.split('.')[-1]
            if type_ not in types:
                continue
            thm = Thm.from_json(proof)
            theorems_list.append(thm)

        graph = GraphFile(file_path, context, theorems_list, None)
        return graph
    

class Graph:
    proj: str
    def __init__(self, files_list: list[GraphFile]):
        self.files_list = files_list


    def get_graph_file(self, file_path: str) -> GraphFile:
        for file in self.files_list:
            if file.file_path == file_path:
                return file
        return None


    def get_thm(self, name: str, file_path: str) -> Thm:
        for file in self.files_list:
            if file.file_path == file_path:
                return file.get_thm(name)
        return None
    
    def get_thm_all_files(self, name: str) -> Thm:
        for file in self.files_list:
            thm = file.get_thm(name)
            if thm is not None:
                return thm
        return None

    def get_thm_by_term(self, term: CtxTerm) -> Thm:
        for file in self.files_list:
            if file.file_path == term.file_path:
                return file.get_thm(term.name)
        return None
    

    def get_accessible_terms(self, file_path: str, names: list[str], lemma_only: bool = True, remove_std: bool = True) -> dict[str, CtxTerm]:
        graph_file = self.get_graph_file(file_path)
        res = {}
        for name in names:
            term = graph_file.context.get_term_by_name(name)
            if term is None:
                continue
            if remove_std and in_std_lib(term.file_path):
                continue
            if lemma_only and not term.is_lemma():
                continue
            res[name] = term
        return res

    def get_definitions_in_thm(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        graph_file = self.get_graph_file(thm.file_path)
        return graph_file.get_definitions_in_thm(thm, remove_std)
    

    def get_lemmas_in_thm(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        graph_file = self.get_graph_file(thm.file_path)
        return graph_file.get_lemmas_in_thm(thm, remove_std)
    

    def get_lemmas_in_thm_recursive(self, thm: Thm, remove_std: bool = True) -> dict[str, Thm]:
        """
        Get all theorems used in a theorem recursively across the entire project.
        If theorem A uses theorem B and theorem B uses theorem C, then
        the result will include both B and C.
        
        Args:
            thm: The theorem to analyze
            remove_std: Whether to remove standard library lemmas
            
        Returns:
            Dictionary mapping theorem names to their Thm representations
        """
        result = {}
        checked_thms = set()
        to_check = [thm]
        
        while to_check:
            current_thm = to_check.pop(0)
            if current_thm.get_full_name() in checked_thms:
                continue
                
            # Get direct lemmas used in this theorem
            graph_file = self.get_graph_file(current_thm.file_path)
            if graph_file is None:
                # Skip if we can't find the file
                checked_thms.add(current_thm.get_full_name())
                continue
                
            lemmas = graph_file.get_lemmas_in_thm(current_thm, remove_std)
            
            # Add these lemmas to our result
            for name, term in lemmas.items():
                if name not in result:
                    result[name] = term
                    
                    # Get the theorem object for this lemma to check its dependencies
                    lemma_thm = self.get_thm_by_term(term)
                    if lemma_thm is not None:
                        to_check.append(lemma_thm)
            
            checked_thms.add(current_thm.get_full_name())

        # Convert result to Thm
        results_thm = {}
        for name, ctx_term in result.items():
            thm = self.get_thm(name, ctx_term.file_path)
            if thm is not None:
                results_thm[name] = thm
        return results_thm
    
    
    def get_definitions_and_lemmas_in_thm(self, thm: Thm, remove_std: bool = True) -> dict[str, CtxTerm]:
        graph_file = self.get_graph_file(thm.file_path)
        return graph_file.get_definitions_and_lemmas_in_thm(thm, remove_std)


    def get_definitions_in(self, name: str, file_path: str, remove_std: bool = True) -> dict[str, CtxTerm]:
        thm = self.get_thm(name, file_path)
        return self.get_definitions_in_thm(thm, remove_std)
    

    def get_lemmas_in(self, name: str, file_path: str, remove_std: bool = True) -> dict[str, CtxTerm]:
        thm = self.get_thm(name, file_path)
        return self.get_lemmas_in_thm(thm, remove_std)


    def get_definitions_and_lemmas_in(self, name: str, file_path: str, remove_std: bool = True) -> dict[str, CtxTerm]:
        thm = self.get_thm(name, file_path)
        return self.get_definitions_and_lemmas_in_thm(thm, remove_std)


    @staticmethod
    def from_proj_datapoint(proj_datapoint_path: str, proj: str):
        Graph.proj = proj

        files_list = []
        files = os.listdir(proj_datapoint_path)
        for file in files:
            file_path = os.path.join(proj_datapoint_path, file)
            graph_file = GraphFile.from_one_datapoint(file_path)
            if len(graph_file.all_theorems_list) > 0:
                files_list.append(graph_file)
        graph = Graph(files_list)
        return graph


    def get_theorems_in_recursive(self, name: str, file_path: str, remove_std: bool = True) -> dict[str, Thm]:
        """
        Get all theorems used in a theorem recursively by name and file path.
        
        Args:
            name: Name of the theorem
            file_path: Path to the file containing the theorem
            remove_std: Whether to remove standard library lemmas
            
        Returns:
            Dictionary mapping theorem names to their Thm representations
        """
        thm = self.get_thm(name, file_path)
        if thm is None:
            return {}
        return self.get_lemmas_in_thm_recursive(thm, remove_std)
    

    def to_local_context_of_thm(self, thm_name: str, file_path: str):
        thm = self.get_thm(thm_name, file_path)
        assert thm is not None

        # remove all theorems after the current theorem in the same file
        graph_file = self.get_graph_file(file_path)
        line = thm.line
        to_remove = set()
        for thm_ in graph_file.all_theorems_list:
            if thm_.line >= line:
                to_remove.add(thm_)
        for thm_ in to_remove:
            graph_file.all_theorems_list.remove(thm_)

        # remove all files that are not imported by the current file
        context = graph_file.context
        all_files = [term.file_path for term in context.terms if not in_std_lib(term.file_path)]
        to_remove = set()
        for file in self.files_list:
            if not file.file_path in all_files:
                to_remove.add(file)

        for file in to_remove:
            self.files_list.remove(file)

        for file in self.files_list:
            print(file.file_path)
            for thm in file.all_theorems_list:
                print(thm.name)


if __name__ == '__main__':
    pass
