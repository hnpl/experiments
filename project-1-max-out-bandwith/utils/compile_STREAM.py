import subprocess
import os
from pathlib import Path
import argparse
from configs.configs import Config
from multiprocessing import Pool, cpu_count
"""
  . Compile STREAM with RISC-V and X86 ISAs.
  . Workflow:
    - Download STREAM if not exists, otherwise pull the repo.
    - Read the chosen element sizes.
    - Compile the workloads.
"""

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

def compile_stream(configs, num_processes):
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

    jobs = []

    for n_elements in n_elements_all:
        jobs.append((n_elements,
                     configs.n_threads,
                     str(stream_repo_path),
                     str(output_path),
                     configs.with_m5_annotations,
                     configs.m5_build_path,
                     configs.m5ops_header_path))

    pool = Pool(num_processes)
    pool.starmap(compiling_helper, jobs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("STREAM builder")
    parser.add_argument("config_path", type=Path, help="Path to the compilation configuration JSON file.")
    parser.add_argument("-j", type=int, default=1, help="Number of processes.")    

    args = parser.parse_args()
    num_processes = args.j

    configs = Config(from_json_file=args.config_path)

    workspace_path = Path(configs.workspace_path)
    workspace_path.mkdir(exist_ok=True)
    os.chdir(configs.workspace_path)

    download_stream(configs)
    compile_stream(configs, num_processes)
