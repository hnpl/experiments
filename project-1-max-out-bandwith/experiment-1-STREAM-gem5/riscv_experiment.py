from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path

import subprocess
import multiprocessing

experiment_tag = "riscv-stream-1"
gem5_binary_path = "/scr/hn/gem5-takekoputa-stream/build/RISCV/gem5.opt"
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-1-STREAM-gem5/configs/gem5/riscvmatched-stream.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-1-STREAM-gem5/results"

def get_md5sum(filepath):
    filepath = str(filepath)
    process_info = subprocess.run(["md5sum", filepath], capture_output=True)
    md5sum = "-1"
    if process_info.returncode == 0:
        md5sum = process_info.stdout.strip().split()[0]
    else:
        print("Warn: md5sum failed for", filepath)
        return None
    return md5sum.decode("utf-8")

# the gem5 binary in /scr/hn/gem5-takekoputa-stream/build/RISCV/gem5.opt in azacca
gem5_binary_md5sum = "2c99f9bd5a4437fb048eb29d79e04bcb"

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())

def output_folder_generator(isa, num_elements, num_cores):
    return "-".join([isa, num_elements, num_cores])

def gem5_params_generator(output_path, stream_binary_path, num_cores):
    gem5_params = {}
    config_params = {}

    """
    gem5-dev/build/RISCV/gem5.opt configs/riscvmatched-stream.py --binary build/binaries/riscv/stream_c.90112 --num_cores 5
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--binary"] = stream_binary_path
    assert(Path(stream_binary_path).exists())
    config_params["--num_cores"] = num_cores

    return gem5_params, config_params

def metadata_generator(stream_binary_md5sum, stream_binary_path, num_elements, num_cores):
    metadata = {}

    metadata["tag"] = experiment_tag
    metadata["git-hash"] = "553096ee5333d646f8a6a0e1ec070f64f1fca498(develop) + c34e1d0c30bb8f7ab839856e815f548d6e422d80(mine)"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "stream-experiments"

    metadata["gem5-binary-md5sum"] = gem5_binary_md5sum
    metadata["stream-binary-md5sum"] = stream_binary_md5sum

    metadata["stream-binary-path"] = stream_binary_path
    metadata["num-elements"] = num_elements
    metadata["num-cores"] = num_cores

    return metadata

def generate_stream_experiment_unit(experiment_tag, stream_binary_path, num_elements, num_cores):
    num_cores = str(num_cores)
    num_elements = str(num_elements)
    assert(isinstance(stream_binary_path, str))
    assert(isinstance(num_cores, str))

    output_folder_name = output_folder_generator("riscv", num_elements, num_cores)
    output_path = str(Path(gem5_output_path_prefix) / experiment_tag / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path, stream_binary_path, num_cores)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = env)

    metadata = metadata_generator(get_md5sum(stream_binary_path), stream_binary_path, num_elements, num_cores)
    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    env = {}
    Path(gem5_output_path_prefix).mkdir(parents=True, exist_ok=True)

    sanity_check()

    experiment = Experiment()

    #for stream_binary_path in Path("build/binaries/riscv/").glob("stream_c.*"):
    #    stream_binary_path = str(stream_binary_path)
    #    unit = generate_stream_experiment_unit(experiment_tag, stream_binary_path=stream_binary_path, num_cores=5)
    #    experiment.add_experiment_unit(unit)

    num_elements_list = []
    with open("riscv_n_elements.txt", "r") as f:
        line = f.readline().strip().split()
        num_elements_list = list(map(int, line))

    for num_elements in num_elements_list:
        stream_binary_path = str(Path(".") / "build" / "binaries" / "riscv" / f"stream_c.{num_elements}")
        unit = generate_stream_experiment_unit(experiment_tag=experiment_tag, stream_binary_path=stream_binary_path, num_elements=num_elements, num_cores=5)
        experiment.add_experiment_unit(unit)

    n_processes = multiprocessing.cpu_count() // 2
    experiment.launch(n_processes)
