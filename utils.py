import os
import json
import re
from datetime import datetime

def extract_code_blocks(response: str) -> list[str]:
    pattern = r'```coq\n(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)
    if matches:
        return [code for code in matches]
    else:
        response = response.strip()
        index = 0
        blocks = []
        while index < len(response):
            start = response.find('```coq', index)
            if start == -1:
                break
            end = response.find('```', start+1)
            if end == -1:
                break
            code = response[start+6:end]
            # tmp fix
            if code.startswith('s '):
                code = 'intros' + code[1:]
            blocks.append(code)
            index = end + 3
        return blocks


def list_files(path: str, postfix: str = '') -> list[str]:
    directory_contents = os.listdir(path)
    files = [entry for entry in directory_contents if os.path.isfile(os.path.join(path, entry))]
    if postfix:
        files = [f for f in files if f.endswith(postfix)]
    return files


def list_files_rec(path: str, postfix: str = ''):
    matching_files = []
    path = path.rstrip('/')
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(postfix):
                matching_files.append(os.path.join(root, file))
    return [f[len(path)+1:] for f in matching_files]


def list_dirs_rec(path: str, postfix: str = ''):
    matching_files = []
    path = path.rstrip('/')
    for root, dirs, _ in os.walk(path):
        for dir in dirs:
            if dir.endswith(postfix):
                matching_files.append(os.path.join(root, dir))
    return [f[len(path)+1:] for f in matching_files]


def create_dirs(file_path: str):
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)


def norm_postfix(file_name: str, target_postfix: str) -> str:
    if target_postfix:
        if '.' in file_name:
            return file_name[:file_name.rfind('.')+1] + target_postfix
        else:
            return file_name + '.' + target_postfix
    else:
        if '.' in file_name:
            return file_name[:file_name.rfind('.')]
        else:
            return file_name


def json_dump(obj, out_file: str):
    out_file = norm_postfix(out_file, 'json')
    create_dirs(out_file)
    json.dump(obj, open(out_file, 'w'))


def json_load(in_file: str):
    in_file = norm_postfix(in_file, 'json')
    return json.load(open(in_file))

def jsonl_load(in_file: str):
    in_file = norm_postfix(in_file, 'jsonl')
    return [json.loads(line) for line in open(in_file)]


def write_file(out_file: str, content: str, mode: str = 'w'):
    create_dirs(out_file)
    with open(out_file, mode=mode) as f:
        f.write(content)


def copy_file(from_file: str, to_file: str = '', content: str = '') -> str:
    if not to_file:
        from_file_parts = from_file.split('/')
        file_name = from_file_parts[-1]
        post_ind = file_name.rfind('.')
        name, post = file_name[:post_ind], file_name[post_ind:]
        timestamp = str(datetime.now().timestamp()).replace('.', '')
        to_file = '/'.join(from_file_parts[:-1] + [name + '_' + timestamp + '_copy' + post])

    create_dirs(to_file)
    write_file(to_file, content)
    return to_file


def copy_file_normal(from_file: str, to_file: str = '', add: str = '') -> str:
    if not to_file:
        from_file_parts = from_file.split('/')
        file_name = from_file_parts[-1]
        post_ind = file_name.rfind('.')
        name, post = file_name[:post_ind], file_name[post_ind:]
        to_file = '/'.join(from_file_parts[:-1] + [name + '_copy' + post])

    create_dirs(to_file)
    with open(from_file, 'r') as f:
        content = f.read()
        if add:
            content = add + '\n' + content
        # content += '\n\nCheck nat.'
    write_file(to_file, content)
    return to_file


def find_datapoint_dir_from_file(full_file_path: str) -> str:
    current_dir = os.path.dirname(full_file_path)
    while current_dir != os.path.dirname(current_dir):
        coqproject_path = os.path.join(current_dir, 'rango_datapoint')
        if os.path.isdir(coqproject_path):
            return coqproject_path
        current_dir = os.path.dirname(current_dir)
    
    coqproject_path = os.path.join(current_dir, 'rango_datapoint')
    if os.path.isdir(coqproject_path):
        return coqproject_path
    return None


def find_coqproject_from_file(full_file_path: str) -> str:
    current_dir = os.path.dirname(full_file_path)
    while current_dir != os.path.dirname(current_dir):
        coqproject_path = os.path.join(current_dir, '_CoqProject')
        if os.path.isfile(coqproject_path):
            return coqproject_path
        current_dir = os.path.dirname(current_dir)
    
    coqproject_path = os.path.join(current_dir, '_CoqProject')
    if os.path.isfile(coqproject_path):
        return coqproject_path
    return None


def get_coq_project_info_from_file(file_full_path: str) -> str:
    coqproject_path = find_coqproject_from_file(file_full_path)
    if coqproject_path is None:
        return None
    
    with open(coqproject_path, 'r') as f:
        lines = f.readlines()
    coqproject_dir = os.path.dirname(coqproject_path)
    lines = [l.strip() for l in lines]
    useful_lines = [l for l in lines if l.startswith('-R') or l.startswith('-Q')]
    options = []
    for line in useful_lines:
        if '#' in line:
            index = line.find('#')
            line = line[:index].strip()
        op, dir_, lp = line.split(' ')
        if dir_ == '.':
            dir_ = coqproject_dir
        else:
            dir_ = os.path.join(coqproject_dir, dir_)
        options.append(f'{op} {dir_},{lp}')
    return ' '.join(options)

