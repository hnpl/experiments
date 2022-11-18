from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path

import subprocess
import multiprocessing

experiment_tag = "riscv-stream-fs-tlb"
gem5_binary_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-2-STREAM-TLB-gem5-fs-baremetal/gem5/build/RISCV/gem5.opt"
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-2-STREAM-TLB-gem5-fs-baremetal/configs/riscv-fs.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-2-STREAM-TLB-gem5-fs-baremetal/results/"
disk_image_path = "/scr/hn/DISK_IMAGES/ubuntu-hpc-riscv.img"

# the gem5 binary @ azacca in /scr/hn/gem5-takekoputa-stream/build/RISCV/gem5.opt
# but I'll use a symlink to put /scr/hn/gem5-takekoputa-stream/ -> experiments/gem5
# the gem5 repo is at https://github.com/takekoputa/gem5
# this binary is compiled off the stream-experiments branch
gem5_binary_md5sum = "fdbe8d70644aab97024f5081b4990621"
disk_image_md5sum = "f4c3d78389462663a9c37f0b90b393f4" # using the same disk image as the npb experiment

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())
    assert(Path(disk_image_path).exists())

def output_folder_generator(isa, num_stream_array_elements, num_cores, num_tlb_entries):
    return "-".join([isa, num_stream_array_elements, num_cores, num_tlb_entries])

def gem5_params_generator(output_path, disk_image_path, num_stream_array_elements, num_cores, num_tlb_entries):
    gem5_params = {}
    config_params = {}

    """
    gem5/build/RISCV/gem5.opt configs/riscv-fs.py --disk_image_path=./riscv-stream-disk.img \
            --num_stream_array_elements=8192 --num_cores=5 --num_tlb_entries 512
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--disk_image_path"] = disk_image_path
    config_params["--num_stream_array_elements"] = num_stream_array_elements
    config_params["--num_cores"] = num_cores
    config_params["--num_tlb_entries"] = num_tlb_entries

    return gem5_params, config_params

def metadata_generator(isa, disk_image_path, num_stream_array_elements, num_cores, num_tlb_entries):
    metadata = {}

    metadata["tag"] = experiment_tag
    metadata["git-hash"] = "a49cba948049b7b8a3a30a586160c8198292ff51(gem5)+657ecf6aba603844e8468a5e1841d9171a31b869(mine)"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "stream-experiments"

    metadata["gem5-binary-md5sum"] = gem5_binary_md5sum
    metadata["disk-image-md5sum"] = disk_image_md5sum

    metadata["isa"] = isa
    metadata["disk_image_path"] = disk_image_path
    metadata["num_stream_array_elements"] = num_stream_array_elements
    metadata["num_tlb_entries"] = num_tlb_entries
    metadata["num_cores"] = num_cores

    return metadata

def generate_stream_experiment_unit(isa, disk_image_path, num_stream_array_elements, num_cores, num_tlb_entries):
    num_stream_array_elements = str(num_stream_array_elements)
    num_cores = str(num_cores)
    num_tlb_entries = str(num_tlb_entries)

    output_folder_name = output_folder_generator(isa, num_stream_array_elements, num_cores, num_tlb_entries)
    output_path = str(Path(gem5_output_path_prefix) / experiment_tag / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path, disk_image_path, num_stream_array_elements, num_cores, num_tlb_entries)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = env)

    metadata = metadata_generator(isa, disk_image_path, num_stream_array_elements, num_cores, num_tlb_entries)
    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    env = {}
    Path(gem5_output_path_prefix).mkdir(parents=True, exist_ok=True)

    sanity_check()

    experiment = Experiment()

    num_elements_list = []
    with open("riscv_n_elements.txt", "r") as f:
        line = f.readline()
        line = line.strip().split()
        num_elements_list = list(map(int, line))
    num_cores_list = [4+1]
    num_tlb_entries_list = [64, 512, 1024, 2048]

    for num_elements in num_elements_list:
        for num_cores in num_cores_list:
            for num_tlb_entries in num_tlb_entries_list:
                unit = generate_stream_experiment_unit(isa = "riscv",
                                                       disk_image_path = disk_image_path,
                                                       num_stream_array_elements = num_elements,
                                                       num_cores = num_cores,
                                                       num_tlb_entries = num_tlb_entries)
                experiment.add_experiment_unit(unit)

    n_processes = 10
    experiment.launch(n_processes)
