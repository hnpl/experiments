import subprocess
import os
from pathlib import Path

"""
  . Compile STREAM with RISC-V and X86 ISAs.
  . Workflow:
    - Download STREAM if not exists, otherwise pull the repo.
    - Read the chosen element sizes.
    - Compile the workloads.
"""

class Config:
    def __init__(self, workspace_path, n_elements_path, stream_repo, isa):
        self.workspace_path = workspace_path
        self.n_elements_path = n_elements_path
        self.stream_repo = stream_repo
        self.isa = isa
        assert(isa in {"riscv", "arm", "x86"})

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

def compile_stream_helper_riscv(n_elements, stream_repo_path, output_path):
    stream_repo_abspath = os.path.abspath(stream_repo_path)
    uid = os.getuid()
    gid = os.getgid()
    command = f"docker run --rm --volume {stream_repo_abspath}:/STREAM -w /STREAM -u {uid}:{gid} -e CC=/riscv/_install/bin/riscv64-unknown-linux-gnu-gcc -e ARRAY_SIZE={n_elements} hn/mpi make"
    output, error = run_cmd(command)
    assert(error is None)
    
    command = f"mv STREAM/stream_c.{n_elements} {output_path}"
    output, error = run_cmd(command)
    assert(error is None)

    return True

def compile_stream(configs):
    stream_repo_path = Path("STREAM")
    output_path = Path("binaries") / Path(configs.isa)
    output_path.mkdir(parents=True, exist_ok=True)
    compiling_helper = None
    if configs.isa == "riscv":
        compiling_helper = compile_stream_helper_riscv
    elif configs.isa == "x86":
        compiling_helper = None
    elif configs.isa == "arm":
        compiling_helper = None
    n_elements_all = None
    with open(configs.n_elements_path, "r") as f:
        line = f.readlines()[0]
        line = line.strip().split()
        n_elements_all = list(map(int, line))
    for n_elements in n_elements_all:
        compiling_helper(n_elements, str(stream_repo_path), str(output_path))

if __name__ == "__main__":
    configs = Config(workspace_path = "build",
                    n_elements_path = os.path.abspath("riscv_n_elements.txt"),
                    stream_repo = "https://github.com/takekoputa/STREAM",
                    isa = "riscv"
                    )
    workspace_path = Path(configs.workspace_path)
    workspace_path.mkdir(exist_ok=True)
    os.chdir(configs.workspace_path)

    download_stream(configs)
    compile_stream(configs)
