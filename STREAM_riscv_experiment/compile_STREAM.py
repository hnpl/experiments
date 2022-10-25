import subprocess
import os
from pathlib import Path

class Config:
    def __init__(self, workspace_path, n_elements_all, stream_repo):
        self.workspace_path = workspace_path[:]
        self.n_elements_all = n_elements_all[:]
        self.stream_repo = stream_repo

def warn(message):
    print(f"warn: {message}")

def run_cmd(command, command_env = {}):
    curr_env = os.environ.copy()
    next_env = {**curr_env, **command_env}
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, env=next_env)
    output, error = process.communicate()
    return output, error

def download_stream(configs):
    clone_path = f"STREAM"
    if os.path.exists(clone_path):
        warn("STREAM folder exists, skip cloning, try pulling")
        os.chdir(f"STREAM")
        command = f"git pull"
        run_cmd(command)
        os.chdir(f"..")
        return None
    command = f"git clone {configs.stream_repo}"
    output, error = run_cmd(command)
    assert(error is None)
    return output

def compile_stream_helper(n_elements, stream_repo_path, output_path):
    stream_repo_abspath = os.path.abspath(stream_repo_path)
    uid = os.getuid()
    gid = os.getgid()
    command = f"docker run --rm --volume {stream_repo_abspath}:/STREAM -w /STREAM -u {uid}:{gid} -e CC=/riscv/_install/bin/riscv64-unknown-linux-gnu-gcc -e ARRAY_SIZE={n_elements} hn/mpi make"
    output, error = run_cmd(command)
    assert(error is None)
    return output

def compile_stream(configs):
    stream_repo_path = Path("STREAM")
    output_path = Path("binaries")
    for n_elements in configs.n_elements_all:
        compile_stream_helper(n_elements, str(stream_repo_path), str(output_path))

if __name__ == "__main__":
    configs = Config(workspace_path = "build",
                    n_elements_all = [2**10],
                    stream_repo = "https://github.com/takekoputa/STREAM"
                    )
    workspace_path = Path(configs.workspace_path)
    workspace_path.mkdir(exist_ok=True)
    os.chdir(configs.workspace_path)

    download_stream(configs)
    compile_stream(configs)
