INITIAL_PROOF_WO_LEMMAS = """You will be given a theorem written in Coq and some related definitions, your job is to write a proof. You should first analyze how to prove it based on the definitions and get a plan. Then, respond your proof in a coq block which starts with "```coq" and ends with "```", following this format:

```coq
{{Proof for the following theorem}}
```

###### Definitions: ######

{definitions}

###### Theorem to prove: ######
```coq
{theorem}
```"""


INITIAL_PROOF_WITH_LEMMAS = """You will be given a theorem written in Coq, with some related definitions and lemmas, your job is to write a proof. You should first analyze how to prove it based on the definitions, and which lemmas can be used. Leverage as more lemmas as possible to facilitate your proof. Then, respond your proof in a coq block which starts with "```coq" and ends with "```", following this format:

```coq
{{Proof for the following theorem}}
```

###### Definitions: ######

{definitions}

###### Lemmas: ######

{lemmas}

###### Theorem to prove: ######
```coq
{theorem}
```"""


REGENERATE_WITH_LEMMAS = """I'm proving a theorem in Coq but got stuck in a proof state. You will be given the theorem statement to prove and the diagnostic information, including the stuck proof state, the erroneous tactic that causes the error, the error message from Coq and the partial proof proceeding the erroneous tactic. Additional context, including related definitions, theorems and lemmas, and a similar theorem with its proof are also provided. First analyze how to prove the theorem based on the provided context, then write a correct proof. You can repair the proof if the error is simple, or generate a new proof if the prior proof is infeasible. Respond your proof in a coq block which starts with "```coq" and ends with "```", following this format:

```coq
<Proof for the following theorem>
```

### Theorem to Prove:
```coq
{theorem}
```

### Stuck Proof State
{proof_state}

### Erroneous Tactic:
```coq
{error_tactic}
```
### Error Message:
{error_msg}

### Partial Proof:
```coq
{partial_proof}
```

### Definitions

{definitions}

### Lemmas

{lemmas}

### Similar Proof
```coq
{similar_proof}
```
"""

REGENERATE_WO_LEMMAS = """I'm proving a theorem in Coq but got stuck in a proof state. You will be given the theorem statement to prove and the diagnostic information, including the stuck proof state, the erroneous tactic that causes the error, the error message from Coq and the partial proof proceeding the erroneous tactic. Additional context, including related definitions, theorems and lemmas, and a similar theorem with its proof are also provided. First analyze how to prove the theorem based on the provided context, then write a correct proof. You can repair the proof if the error is simple, or generate a new proof if the prior proof is infeasible. Respond your proof in a coq block which starts with "```coq" and ends with "```", following this format:

```coq
<Proof for the following theorem>
```

### Theorem to Prove:
```coq
{theorem}
```

### Stuck Proof State
{proof_state}

### Erroneous Tactic:
```coq
{error_tactic}
```
### Error Message:
{error_msg}

### Partial Proof:
```coq
{partial_proof}
```

### Definitions

{definitions}

### Lemmas

{lemmas}

### Similar Proof
```coq
{similar_proof}
```
"""