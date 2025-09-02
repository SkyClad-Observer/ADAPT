# ADAPT
Adaptive Proof Refinement with LLM-Guided Strategy Selection

# Dependencies
- OPAM
- Anaconda
- coq-lsp
- CoqPyt

# Install
```
# Create Anaconda env
conda env create adapt python=3.11

# Create OPAM switch
opam switch create adapt 5.3.0

# Install Coq and libraries
opam pin add coq 8.18.0
opam install coq-lsp
opam install coq-hammer

# Install CoqPyt
git clone https://github.com/sr-lab/coqpyt.git
cd coqpyt
pip install -r requirements.txt
python -m pip install -e .
```

# Evaluate
```
python -m run \
    --exp_name="<name of experiment>" \
    --proj="<project to evaluate>" \
    --model="<model name>" \
    --temp="<model temperature>"　\
    --top_p="<model top p>"
    --resume="<name of an experiment, reuse initial proof in that experiment if specified>" \
    --processes="<number of threads>"
```