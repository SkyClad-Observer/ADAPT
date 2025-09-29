PROPOSE_LEMMAS_WO_LEMMAS = """We are proving a theorem in Coq but get stuck in a proof state, your task is to propose some new lemma statements to help solve it. You will be given the theorem statement and proof state, together with related definitions, existing theorem and lemmas. Your lemmas must state new, non-trivial properties. For each proposed lemma statement, explain why it is correct and useful.
## Example
### Proof state:
Hypothesis:
il_0, il_1, il_2: list nat
u_0: nat
H1: concat il_0 il_1) = il_2
H2: list_member il_0 u_0
H3: not (list_member il_0 u_0) /\ (list_member il_2 u_0)
Goal:
(list_member il_1 u_0)

### Definitions:
Inductive list_member: list nat -> nat -> Prop :=
| lmem1: forall l u u', u = u' -> list_member (u :: l) u'
| lmem2: forall l u v, list_member l u -> list_member (v :: l) u.

### Your response:
Analysis:
1. From (list_member il_2 u_0), we know u_0 appears in the concatenated (list il_0 ++ il_1).  
2. Being a member of (il_0 ++ il_1) means u_0 must be either in il_0 or in il_1.  
3. However, we are also given that, not (list_member il_0, u_0), which means u_0 does not appear in il_0.  
4. Therefore, the only possibility left is that u_0 is in il_1, Hence (list_member il_1 u_0) must hold.

Thought 1:
It is useful to have a lemma about the membership of a number in a concatenated list.

Lemma 1:
```coq
Lemma list_member_app : forall (il_0 il_1 il_2 : list nat) (u : nat), 
  il_2 = (concat il_0 il_1) -> list_member il_2 u -> list_member il_0 u \/ list_member il_1 u.
```

## Propose lemmas for the following proof state:
### Proof state:
{proof_state}

### Definitions:
{definitions}

### Your response:"""


PROPOSE_LEMMAS_WITH_LEMMAS = """We are proving a theorem in Coq but get stuck in a proof state, your task is to propose some new lemma statements to help solve it. You will be given the theorem statement and proof state, together with related definitions, existing theorem and lemmas. Your lemmas must state new, non-trivial properties. For each proposed lemma statement, explain why it is correct and useful.
## Example
### Proof state:
Hypothesis:
il_0, il_1, il_2: list nat
u_0: nat
H1: concat il_0 il_1) = il_2
H2: list_member il_0 u_0
H3: not (list_member il_0 u_0) /\ (list_member il_2 u_0)
Goal:
(list_member il_1 u_0)

### Definitions:
Inductive list_member: list nat -> nat -> Prop :=
| lmem1: forall l u u', u = u' -> list_member (u :: l) u'
| lmem2: forall l u v, list_member l u -> list_member (v :: l) u.

### Your response:
Analysis:
1. From (list_member il_2 u_0), we know u_0 appears in the concatenated (list il_0 ++ il_1).  
2. Being a member of (il_0 ++ il_1) means u_0 must be either in il_0 or in il_1.  
3. However, we are also given that, not (list_member il_0, u_0), which means u_0 does not appear in il_0.  
4. Therefore, the only possibility left is that u_0 is in il_1, Hence (list_member il_1 u_0) must hold.

Thought 1:
It is useful to have a lemma about the membership of a number in a concatenated list.

Lemma 1:
```coq
Lemma list_member_app : forall (il_0 il_1 il_2 : list nat) (u : nat), 
  il_2 = (concat il_0 il_1) -> list_member il_2 u -> list_member il_0 u \/ list_member il_1 u.
```

## Propose lemmas for the following proof state:
### Proof state:
{proof_state}

### Definitions:
{definitions}

### Existing Lemmas:
{lemmas}

### Your response:"""

PROPOSE_LEMMAS_WO_LEMMAS_0_SHOT = """We are proving a theorem in Coq but get stuck in a proof state, your task is to propose some new lemma statements to help solve it. You will be given the theorem statement and proof state, together with related definitions, existing theorem and lemmas. Your lemmas must state new, non-trivial properties. For each proposed lemma statement, explain why it is correct and useful.
Response in the following format:
{{Analysis on how to solve the proof state}}

```coq
Lemma lemma_1 : ...
```
{{Explaination for lemma_1}}

```coq
Lemma lemma_2 : ...
```
{{Explaination for lemma_2}}
...

Propose lemmas for the following proof state:
### Proof state: 

{proof_state}

### Definitions: 

{definitions}"""

PROPOSE_LEMMAS_WITH_LEMMAS_0_SHOT = """We are proving a theorem in Coq but get stuck in a proof state, your task is to propose some new lemma statements to help solve it. You will be given the theorem statement and proof state, together with related definitions, existing theorem and lemmas. Your lemmas must state new, non-trivial properties. For each proposed lemma statement, explain why it is correct and useful.
{{Analysis on how to solve the proof state}}

```coq
Lemma lemma_1 : ...
```
{{Explaination for lemma_1}}

```coq
Lemma lemma_2 : ...
```
{{Explaination for lemma_2}}
...

Propose lemmas for the following proof state:
### Proof state:

{proof_state}

### Definitions:

{definitions}

### Existing lemmas:

{lemmas}"""


REFINE_LEMMAS = """We are proving a theorem in Coq but get stuck in a proof state, your task is to refine an existing lemma to help solve it. You will be given the theorem statement to prove, the stuck proof state, related definitions and the specific lemma to refine, including its proof. A set of existing theorems and lemmas are also provided. First analyze how to adapt this given lemma to help solve the proof goal, then produce the refined lemma statement together with its proof. Try to reuse the original proof of the given lemma where possible.
### Theorem to prove:
{theorem}

### Proof state:
{proof_state}

### Definitions:
{definitions}

### Existing Lemmas:
{lemmas}

### Lemma to Refine:

{lemma_to_refine}"""
