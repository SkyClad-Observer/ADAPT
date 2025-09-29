import os
from utils import list_files_rec
import shutil

#################################### BUILD INSTRUCTIONS ####################################

proj_links = {
    'fav-ssr': 'https://github.com/coq-community/fav-ssr.git',
    'types-and-proofs': 'https://github.com/TiarkRompf/types-and-proofs.git',
    'PnVRocqLib': 'https://github.com/PnVDiscord/PnVRocqLib.git',
    'typed_tree_calculus': 'https://github.com/barry-jay-personal/typed_tree_calculus.git',
    'LHL': 'https://github.com/ehatti/LHL.git',
    'FormArith': 'https://github.com/bwerner/FormArith.git',
    'busycoq': 'https://github.com/meithecatte/busycoq.git',
    'lregex': 'https://github.com/Agnishom/lregex.git',
    'CoqCP': 'https://github.com/huynhtrankhanh/CoqCP.git',
    'gitrees': 'https://github.com/logsem/gitrees.git',
    'rbtree': 'https://github.com/Hyperb0rean/rbtree.git',
    'regexes': 'https://github.com/ngernest/regexes.git',
    'finite': 'https://github.com/mb64/finite.git',
    'coq-bst': 'https://github.com/Dessertion/coq-bst.git',
    'tilogics': 'https://github.com/decrn/tilogics.git',
}


def build_fav_ssr(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.17'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'make clean', f'make -j {n_jobs}']

def build_types_and_proofs(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    cwd = os.path.join(path, 'pub')
    coq_project = os.path.join(cwd, '_CoqProject')

    files = [f for f in os.listdir(cwd) if f.endswith('.v') and not f.endswith('_copy.v') and 'coqpyt' not in f]
    with open(coq_project, 'w') as f:
        f.write("-R . Top\n")
        for file in files:
            f.write(file + '\n')
    
    file = 'stlc_refb_effb_equiv.v'
    file_path = os.path.join(cwd, file)
    if os.path.exists(file_path):
        content = open(file_path, 'r').read()
        content = content.replace('}.', '}')
        with open(file_path, 'w') as f:
            f.write(content)

    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'
    return cwd, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']


def build_pnvrocqlib(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    if commit_time is None or commit_time < 1735475611:
        version = 'coqllm8.18'
    else:
        version = 'coqllm8.20'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']


def build_typed_tree_calculus(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'

    if commit == 'f2477622c03e37c0e959403360c693a11f26333e':
        file_path = os.path.join(path, 'types.v')
        content = open(file_path, 'r').read()
        lines = content.split('\n')
        remove_line_num = 794
        lines = lines[:remove_line_num] + lines[remove_line_num+1:]
        content = '\n'.join(lines)
        with open(file_path, 'w') as f:
            f.write(content)

    return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']

def build_LHL(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'
    makefile = 'coq_makefile -f _CoqProject -o Makefile'

    return path, [switch_version, makefile, 'make clean', f'make -j {n_jobs}']

def build_FormArith(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.19'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'dune clean', 'dune build']

def build_staged(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'make clean', f'make -j {n_jobs}']

def build_busycoq(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'
    cwd = os.path.join(path, 'verify')
    if os.path.exists(cwd):
        Skelet17 = os.path.join(cwd, 'Skelet17.v')
        if os.path.exists(Skelet17):
            os.remove(Skelet17)
        files = list_files_rec(cwd, '.v')
        coq_project = os.path.join(cwd, '_CoqProject')
        with open(coq_project, 'w') as f:
            f.write('-Q . BusyCoq\n')
            for file in files:
                f.write(file + '\n')
        return cwd, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']
    else:
        Skelet17 = os.path.join(path, 'Skelet17.v')
        if os.path.exists(Skelet17):
            os.remove(Skelet17)
        files = list_files_rec(path, '.v')
        coq_project = os.path.join(path, '_CoqProject')
        with open(coq_project, 'w') as f:
            f.write('-Q . BusyCoq\n')
            for file in files:
                f.write(file + '\n')
        return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']


def build_lregex(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'
    cwd = os.path.join(path, 'theories')
    return cwd, [switch_version, 'make clean', f'make -j {n_jobs}']


def build_CoqCP(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    to_remove = [
        "theories/FillInTheBlanks.v",
        "theories/TwoWaysToFill.v",
        "theories/DisjointSetUnionCode2.v",
        "theories/DisjointSetUnionCode3.v",
        "theories/BubbleSortTest.v",
        "theories/RegularBracketString.v"
    ]
    version = 'coqllm8.17'
    switch_version = f'eval $(opam env --switch={version})'

    files = list_files_rec(path, '.v')
    for file in files:
        if file in to_remove:
            os.remove(os.path.join(path, file))
            continue
        file_path = os.path.join(path, file)
        content = open(file_path, 'r').read()
        lines = content.split('\n')
        lines = [l.replace('Hint Rewrite', '#[export] Hint Rewrite') if l.startswith('Hint Rewrite') else l for l in lines]
        content = '\n'.join(lines)
        with open(file_path, 'w') as f:
            f.write(content)
    coq_project = os.path.join(path, '_CoqProject')
    if not os.path.exists(coq_project):
        return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']
    
    content = open(coq_project, 'r').read()
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        line_ = line.strip()
        if line_ in to_remove:
            continue
        new_lines.append(line_)
    content = '\n'.join(new_lines)
    with open(coq_project, 'w') as f:
        f.write(content)
    return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']


def build_gitrees(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'

    return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']


def build_rbtree(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.18'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'coq_makefile -f _CoqProject -o Makefile', 'make clean', f'make -j {n_jobs}']


def build_regexes(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'regexes'
    switch_version = f'eval $(opam env --switch={version})'
    cwd = os.path.join(path, 'coq')
    old_path = os.path.join(cwd, 'old')
    if os.path.exists(old_path):
        shutil.rmtree(old_path)
    return cwd, [switch_version, 'make clean', f'make -j {n_jobs}']


def build_finite(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.19'
    switch_version = f'eval $(opam env --switch={version})'
    file_path = os.path.join(path, 'finite.v')
    content = open(file_path, 'r').read()
    if 'End Semantics.' not in content:
        with open(file_path, 'w') as f:
            f.write(content + '\n\nEnd Semantics.')
    return path, [switch_version, f'coqc finite.v']


def build_coq_bst(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.20'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'make clean', f'make -j {n_jobs}']


def build_tilogics(path: str, commit: str, commit_time: int, n_jobs: int = 8) -> tuple[str, list[str]]:
    version = 'coqllm8.17'
    switch_version = f'eval $(opam env --switch={version})'
    return path, [switch_version, 'make clean', f'make -j {n_jobs}']

build_instructions = {
    'fav-ssr': build_fav_ssr,
    'types-and-proofs': build_types_and_proofs,
    'PnVRocqLib': build_pnvrocqlib,
    'typed_tree_calculus': build_typed_tree_calculus,
    'LHL': build_LHL,
    'FormArith': build_FormArith,
    'busycoq': build_busycoq,
    'lregex': build_lregex,
    'CoqCP': build_CoqCP,
    'gitrees': build_gitrees,
    'regexes': build_regexes,
    'finite': build_finite,
    'coq-bst': build_coq_bst,
    'tilogics': build_tilogics,
}


def get_build_intructions(path: str, proj: str, commit: str, commit_time: int, n_jobs: int) -> tuple[str, list[str]]:
    # proj = proj.replace('-', '_')
    method = build_instructions[proj]
    return method(path, commit, commit_time, n_jobs)


#################################### _CoqProject INFO ####################################

def find_coqproject_from_file(full_file_path: str):
    # Get the directory of the .v file
    current_dir = os.path.dirname(full_file_path)
    
    # Iterate upwards through the directory structure
    while current_dir != os.path.dirname(current_dir):  # Stop at the root directory
        # Check if _CoqProject exists in the current directory
        coqproject_path = os.path.join(current_dir, '_CoqProject')
        if os.path.isfile(coqproject_path):
            return coqproject_path
        
        # Move up to the parent directory
        current_dir = os.path.dirname(current_dir)
    
    # Check the root directory one last time
    coqproject_path = os.path.join(current_dir, '_CoqProject')
    if os.path.isfile(coqproject_path):
        return coqproject_path
    
    # If no _CoqProject file is found, return None
    return None


def find_coqproject(project_path: str, file_path: str) -> str:
    full_file_path = os.path.join(project_path, file_path)
    path_components = os.path.normpath(full_file_path).split(os.sep)
    current_path = project_path
    for component in path_components:
        current_path = os.path.join(current_path, component)
        coqproject_path = os.path.join(current_path, '_CoqProject')
        if os.path.isfile(coqproject_path):
            return coqproject_path
    return None


def get_coq_project_info_from_file(file_full_path: str) -> str:
    coqproject_path = find_coqproject_from_file(file_full_path)
    if coqproject_path is None:
        return ''
    
    with open(coqproject_path, 'r') as f:
        lines = f.readlines()
    coqproject_dir = os.path.dirname(coqproject_path)
    lines = [l.strip() for l in lines]
    useful_lines = [l for l in lines if l.startswith('-R') or l.startswith('-Q')]
    options = []
    for line in useful_lines:
        if '#' in line:
            line = line.split('#')[0].strip()
        op, dir_, lp = line.split(' ')
        if dir_ == '.':
            dir_ = coqproject_dir
        else:
            dir_ = os.path.join(coqproject_dir, dir_)
        options.append(f'{op} {dir_},{lp}')
    return ' '.join(options)


def get_coq_project_info(proj: str, file: str) -> str:
    file_full_path = os.path.join(proj, file)
    return get_coq_project_info_from_file(file_full_path)
