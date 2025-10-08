# create opam switch
opam switch create coqllm8.17 5.1.0
# set opam switch
opam switch set coqllm8.17
eval $(opam env --switch=coqllm8.17) 
# install Coq
opam pin add coq 8.17.0
# install dependencies
opam install coq-lsp coq-hammer

# create switches for Coq 8.18, 8.19, 8.20 with similar commands
opam switch create coqllm8.18 5.1.0
opam switch set coqllm8.18
eval $(opam env --switch=coqllm8.18) 
opam pin add coq 8.18.0
opam install coq-lsp coq-hammer

opam switch create coqllm8.19 5.1.0
opam switch set coqllm8.19
eval $(opam env --switch=coqllm8.19) 
opam pin add coq 8.19.0
opam install coq-lsp coq-hammer

opam switch create coqllm8.20 5.1.0
opam switch set coqllm8.20
eval $(opam env --switch=coqllm8.20) 
opam pin add coq 8.20.0
opam install coq-lsp coq-hammer
