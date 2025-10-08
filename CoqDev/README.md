# CoqDev
Coq proof generation benchmark

# Projects
| Name | Link |
| --- | --- |
| fav-ssr | https://github.com/coq-community/fav-ssr.git |
| types-and-proofs | https://github.com/TiarkRompf/types-and-proofs.git |
| PnVRocqLib | https://github.com/PnVDiscord/PnVRocqLib.git |
| typed_tree_calculus | https://github.com/barry-jay-personal/typed_tree_calculus.git |
| LHL | https://github.com/ehatti/LHL.git |
| FormArith | https://github.com/bwerner/FormArith.git |
| busycoq | https://github.com/meithecatte/busycoq.git |
| lregex | https://github.com/Agnishom/lregex.git |
| CoqCP | https://github.com/huynhtrankhanh/CoqCP.git |
| gitrees | https://github.com/logsem/gitrees.git |
| rbtree | https://github.com/Hyperb0rean/rbtree.git |
| regexes | https://github.com/ngernest/regexes.git |
| finite | https://github.com/mb64/finite.git |
| coq-bst | https://github.com/Dessertion/coq-bst.git |
| tilogics | https://github.com/decrn/tilogics.git |

Please refer to `dataset/project_name/eval_commits_theorems.json` for the theorems in each project.

# Build 
### Install Coq 
```
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
# or refer to install.sh
```

```
python -m build.run
```