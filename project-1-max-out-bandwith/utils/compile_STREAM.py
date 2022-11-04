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
    def __init__(self, workspace_path, n_elements_path, stream_repo, isa, n_threads, with_m5_annotations, m5_build_abspath, m5ops_header_abspath):
        self.workspace_path = workspace_path
        self.n_elements_path = n_elements_path
        self.stream_repo = stream_repo
        self.isa = isa
        assert(isa in {"riscv", "arm", "x86"})
        self.n_threads = n_threads
        self.with_m5_annotations = with_m5_annotations
        self.m5_build_abspath = m5_build_abspath
        self.m5ops_header_abspath = m5ops_header_abspath

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

def compile_stream_helper_riscv(n_elements, n_threads, stream_repo_path, output_path, with_m5_annotations, m5_build_abspath, m5ops_header_abspath):
    stream_repo_abspath = os.path.abspath(stream_repo_path)

    # some hardcoded vals
    guest_m5_build_path = "/m5_build"
    guest_m5ops_header_path = "/m5ops_header"
    guest_STREAM_path = "/STREAM"
    guest_compiler_path = "/riscv/_install/bin/riscv64-unknown-linux-gnu-gcc"
    docker_image = "hn/mpi"
    workspace_path = guest_STREAM_path

    # getting the right uid and gid
    uid = os.getuid()
    gid = os.getgid()

    # linking directory from host to guest
    directory_links = [f"{stream_repo_abspath}:{guest_STREAM_path}"] 
    if with_m5_annotations:
        directory_links.append(f"{m5_build_abspath}:{guest_m5_build_path}")
        directory_links.append(f"{m5ops_header_abspath}:{guest_m5ops_header_path}")
    # convert the links to a string
    directory_link_str = ""
    for link in directory_links:
        directory_link_str += f"--volume {link} "

    # setting up the environment variables
    env = {}
    env["CC"] = guest_compiler_path
    env["ARRAY_SIZE"] = n_elements
    env["N_THREADS"] = n_threads
    if with_m5_annotations:
        env["M5_BUILD_PATH"] = guest_m5_build_path
        env["M5OPS_HEADER_PATH"] = guest_m5ops_header_path
    # constructing the string specifying the environment variables
    env_str = ""
    for key, val in env.items():
        env_str += f"-e {key}={val} "

    command = f"docker run --rm {directory_link_str} -w {workspace_path} -u {uid}:{gid} {env_str} {docker_image} make"
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
        compiling_helper(n_elements=n_elements,
                         n_threads=configs.n_threads,
                         stream_repo_path=str(stream_repo_path),
                         output_path=str(output_path),
                         with_m5_annotations=configs.with_m5_annotations,
                         m5_build_abspath=configs.m5_build_abspath,
                         m5ops_header_abspath=configs.m5ops_header_abspath)

if __name__ == "__main__":
    configs = Config(workspace_path = "build",
                    n_elements_path = os.path.abspath("riscv_n_elements.txt"),
                    stream_repo = "https://github.com/takekoputa/STREAM",
                    isa = "riscv",
                    n_threads=4,
                    with_m5_annotations=True,
                    m5_build_abspath=os.path.abspath("gem5/util/m5/build/riscv/"),
                    m5ops_header_abspath=os.path.abspath("gem5/include/")
                    )
    workspace_path = Path(configs.workspace_path)
    workspace_path.mkdir(exist_ok=True)
    os.chdir(configs.workspace_path)

    download_stream(configs)
    compile_stream(configs)
