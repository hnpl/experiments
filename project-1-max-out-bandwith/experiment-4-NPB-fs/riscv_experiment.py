from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path

import subprocess
import multiprocessing

experiment_tag = "riscv-npb-fs"
gem5_binary_path = "/scr/hn/gem5-takekoputa-stream/build/RISCV/gem5.opt"
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-4-NPB-fs/configs/gem5/riscvmatched-npb.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-4-NPB-fs/results/"
disk_image_path = "/scr/hn/DISK_IMAGES/ubuntu-hpc-riscv.img"

# the gem5 binary @ azacca in /scr/hn/gem5-takekoputa-stream/build/RISCV/gem5.opt
# but I'll use a symlink to put /scr/hn/gem5-takekoputa-stream/ -> experiments/gem5
# the gem5 repo is at https://github.com/takekoputa/gem5
# this binary is compiled off the stream-experiments branch
gem5_binary_md5sum = "fdbe8d70644aab97024f5081b4990621"
disk_image_md5sum = "f4c3d78389462663a9c37f0b90b393f4"

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())
    assert(Path(disk_image_path).exists())

def output_folder_generator(isa, workload, workload_class, num_cores):
    return "-".join([isa, workload, workload_class, num_cores])

def gem5_params_generator(output_path, disk_image_path, workload, workload_class, num_cores):
    gem5_params = {}
    config_params = {}

    """
    gem5/build/RISCV/gem5.opt configs/gem5/riscvmatched-npb.py \
        --disk_image_path /scr/hn/DISK_IMAGES/ubuntu-hpc-riscv.img \
        --workload ft \
        --workload_class A \
        --num_cores 5
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--disk_image_path"] = disk_image_path
    config_params["--workload"] = workload
    config_params["--workload_class"] = workload_class
    config_params["--num_cores"] = num_cores

    return gem5_params, config_params

def metadata_generator(isa, disk_image_path, workload, workload_class, num_cores):
    metadata = {}

    metadata["tag"] = experiment_tag
    metadata["git-hash"] = "a49cba948049b7b8a3a30a586160c8198292ff51(gem5)+657ecf6aba603844e8468a5e1841d9171a31b869(mine)"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "npb-experiments"

    metadata["gem5-binary-md5sum"] = gem5_binary_md5sum
    metadata["disk-image-md5sum"] = disk_image_md5sum

    metadata["isa"] = isa
    metadata["disk_image_path"] = disk_image_path
    metadata["benchmark_suite"] = "NPB3.4-OMP"
    metadata["workload"] = workload
    metadata["workload_class"] = workload_class
    metadata["num_cores"] = num_cores

    return metadata

def generate_stream_experiment_unit(isa, disk_image_path, workload, workload_class, num_cores):
    num_cores = str(num_cores)

    output_folder_name = output_folder_generator(isa, workload, workload_class, num_cores)
    output_path = str(Path(gem5_output_path_prefix) / experiment_tag / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path, disk_image_path, workload, workload_class, num_cores)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = env)

    metadata = metadata_generator(isa, disk_image_path, workload, workload_class, num_cores)
    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    env = {}
    Path(gem5_output_path_prefix).mkdir(parents=True, exist_ok=True)

    sanity_check()

    experiment = Experiment()

    num_cores_list = [4+1]

    for workload in ["mg", "ft"]:
        for workload_class in ["S", "W", "A", "B", "C"]:
            for num_cores in num_cores_list:
                unit = generate_stream_experiment_unit(isa = "riscv",
                                                       disk_image_path = disk_image_path,
                                                       workload = workload,
                                                       workload_class = workload_class,
                                                       num_cores = num_cores)
                experiment.add_experiment_unit(unit)

    n_processes = 10
    experiment.launch(n_processes)
