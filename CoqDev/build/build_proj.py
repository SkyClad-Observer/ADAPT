import os
import subprocess
import git
import json
from .proj_info import get_build_intructions, proj_links


def filter_errors_only(log_text: str) -> str:
    lines = log_text.splitlines(keepends=True)
    output_lines = []
    
    # We'll track whether we are currently "inside" an error block or a warning block.
    in_error_block = False
    in_warning_block = False
    
    for line in lines:
        # Check if a new block starts
        if line.startswith("Error:"):
            # Switch to error-block mode
            in_error_block = True
            in_warning_block = False
            output_lines.append(line)  # Keep the "Error: ..." line itself

        elif line.startswith("Warning:"):
            # Switch to warning-block mode
            in_error_block = False
            in_warning_block = True
        else:
            if in_error_block:
                output_lines.append(line)
            elif not in_warning_block:
                output_lines.append(line)

    return "".join(output_lines)


def clone_repo(proj: str, path: str):
    """
    run git clone for the project in path
    """
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        return
    link = proj_links[proj]
    subprocess.run(["git", "clone", link], cwd=path)

    if proj in ['logrel-coq']:
        path = os.path.join(path, proj)
        subprocess.run(["git", "submodule", "init"], cwd=path)
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=path)


def run_build(path: str, proj: str, commit: str, commit_time: int, n_jobs: int) -> tuple[bool, str, str]:
    cwd, instructions = get_build_intructions(path, proj, commit, commit_time, n_jobs)
    if cwd is None or instructions is None:
        return False, 'skipped', 'skipped'
    print(f"Building {path}")
    instr = '; '.join(instructions)
    result = subprocess.run(
        instr, cwd=cwd, capture_output=True, shell=True
    )
    if result.returncode != 0:
        print(
            f"Failed to build {path}. To debug, run: {instr}."
        )
        error_msg = result.stderr.decode()
        filter_error_msg = filter_errors_only(error_msg)
        print(filter_error_msg)
        return False, error_msg, filter_errors_only(filter_error_msg)
    print(f"Successfully built {path}")
    return True, '', ''


def clone_and_build(proj: str, path: str, commit: str):
    commit_path = os.path.join(path, commit)
    clone_repo(proj, commit_path)
    proj_path = os.path.join(commit_path, proj)
    
    proj_meta = json.load(open(os.path.join('./dataset', proj, 'meta.json')))
    commit_time = proj_meta['commits_info'][commit]['commit_time']
    repo = git.Repo(proj_path)
    repo.git.checkout(commit, "-f")
    success, error_msg, filter_error_msg = run_build(proj_path, proj, commit, commit_time, 16)
    return success, error_msg, filter_error_msg


if __name__ == '__main__':
    pass
