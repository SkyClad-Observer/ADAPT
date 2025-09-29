DECISIONS_INSTRUCTION = """
Analyze the provided information, then choose one of the following actions:

1. **Lemma Discovery**
   Description: Propose new lemmas or refine existing ones to help the proof. 
   **Action:** List keywords that we want to search for (in the current environment and the previous commit). The keywords can be names of definitions (thus lemmas with these definitions in their statements are found) or names of lemmas used in the similar proof.
   **Response Format if Chosen:**
   ```Lemma Discovery; [name_1, name_2 ...]```

2. **Context Enrichment**  
   Description: Retrieve more relevant definitions, lemmas, theorems, and proofs from the project and imported files. 
   **Response Format if Chosen:**
   ```Context Enrichment; [keyword_1, keyword_2, ...]```

3. **Regenerate**
   Description: Directly regenerate the proof if the current context seems sufficient or the previous proof is unpromising.
   **Response Format if Chosen:**  
   ```Regeneration```

After your analysis, start your response with the "### Action" line indicating one of the three options: **Lemma Discovery**, **Context Enrichment**, or **Regenerate**. Then provide the corresponding action-specific details, as specified in the **Response Format if Chosen:**.
"""

DECISION_MAKING_INITIAL = """
We are proving a theorem in Coq but get stuck in a proof state, your need to select a refinement strategy to fix it. You will be provided with the theorem, and the diagnostic information, including the stuck proof state, the erroneous tactic that causes the error, the error message from Coq and the partial proof proceeding the erroneous tactic. Additional supporting context, including related definitions and lemmas, and a similar theorem with its proof are also provided.

### Theorem:
```coq
{theorem}
```

### Definitions:
{definitions}

### Proof State:
{proof_state}

### Partial Proof:
```coq
{partial_proof}
```

### Lemmas:
{lemmas}

### Most Similar Theorem:
```coq
{similar_theorem}
```

""" + DECISIONS_INSTRUCTION

### Lemma Retrieval ###

RETRIEVED_EXTRA_LEMMAS = """We have retrieved lemmas using the keywords:
### Lemmas in Current Environment
{lemmas_current}

### Lemmas Only in Previous Commit
{lemmas_previous}

Note that, a lemma is listed in ### Lemmas in Current Environment if it is both in the current environment and previous commit."""


NO_MORE_LEMMAS = """We failed to retrieve any more lemmas given these keywords. Now, you should try lemma discovery or regenerate the proof."""


### Lemma Discovery and Refinement ###
NEW_LEMMA_DISCOVERY_REFINED = """We have refined some lemmas from previous commit, and discovered some new lemmas in current environment:

### Refined Lemmas from Previous Commit
{refined_lemmas}

### Discovered Lemmas
{new_lemmas}"""

NO_NEW_LEMMAS = """We failed to discover any new lemmas. Now, you can try lemma discovery again or regenerate the proof."""


### Regenerate ###

REGENERATE_FEEDBACK = """A new proof has been generated, but the proof is not correct. The generated proof, the partial proof and the stuck proof state are provided as follows. The wrong tactic (applied in the stuck state) and error message are also provided:
### Generated Proof
```coq
{generated_proof}
```

### Partial Proof
```coq
{partial_proof}
```

### StuckProof State
{proof_state}

### Wrong Tactic
{error_tactic}

### Error Message
{error_msg}
"""
