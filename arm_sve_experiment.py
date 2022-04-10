from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path

import subprocess

experiment_tag = "bougainvillea-1"
gem5_binary_path = "/home/hn/gem5/build/ARM/gem5.opt"
gem5_config_path = "/home/hn/gem5/configs/example/arm/fs_xsbench.py"
gem5_output_path_prefix = "/home/hn/experiment-results/arm_sve_xsbench/"
env = {'M5_PATH': '/home/hn/gem5/arm-system/'}
disk_image_path = "/home/hn/disk-images/arm64-ubuntu-xsbench.img"

def get_md5sum(filepath):
    filepath = str(filepath)
    process_info = subprocess.run(["md5sum", filepath], capture_output=True)
    md5sum = "-1"
    if process_info.returncode == 0:
        md5sum = process_info.stdout.strip().split()[0]
    else:
        print("Warn: md5sum failed for", filepath)
    return md5sum

disk_image_hash = get_md5sum(disk_image_path)
#disk_image_md5sum = "f6accfd7ff1e07b4ae3dc13b78e80635"
#gem5_binary_md5sum = "beaf1c069ac9226fc60d8d4b2fb5ec72"

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())
    assert(Path(env['M5_PATH']).exists())
    assert(Path(disk_image_path).exists())

def output_folder_generator(cpu_type, vl, benchmark_size, benchmark_threads):
    return "_".join([experiment_tag, cpu_type, vl, benchmark_size, benchmark_threads])

def gem5_params_generator(output_path, cpu_type, vl, benchmark_size, benchmark_threads):
    gem5_params = {}
    config_params = {}

    """
    build/ARM/gem5.opt configs/example/arm/fs_xsbench.py \
        --disk-image=/home/hn/disk-images/arm64-ubuntu-xsbench.img \
        --sve-vl=1 --benchmark-size=small --benchmark_threads=1 \
        --cpu=atomic --num-cores=1
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--disk-image"] = disk_image_path
    config_params["--cpu"] = cpu_type
    config_params["--num-cores"] = benchmark_threads
    config_params["--sve-vl"] = vl
    config_params["--benchmark-size"] = benchmark_size
    config_params["--benchmark-threads"] = benchmark_threads

    return gem5_params, config_params

def metadata_generator():
    metadata = {}

    metadata["tag"] = experiment_tag
    metadata["git-hash"] = "a4bf91bd960f0d59a820efd1a1659860e1aebb19"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "xsbench"

    #metadata["gem5-binary-md5sum"] = gem5_binary_md5sum
    #metadata["disk-image-md5sum"] = disk_image_md5sum

    return metadata

def generate_XSBench_experiment_unit(cpu_type, vl, benchmark_size, benchmark_threads, env):
    assert(isinstance(cpu_type, str))
    assert(isinstance(vl, str))
    assert(isinstance(benchmark_size, str))
    assert(isinstance(benchmark_threads, str))

    output_folder_name = output_folder_generator(cpu_type, vl, benchmark_size, benchmark_threads)
    output_path = str(Path(gem5_output_path_prefix) / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path, cpu_type, vl, benchmark_size, benchmark_threads)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = env)

    metadata = metadata_generator()
    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    sanity_check()

    cpu_types = ["atomic", "timing"]
    vls = list(range(17))
    sizes = ["small"]
    n_threads = [1, 2, 4]

    env = {'M5_PATH': '/home/hn/gem5/arm-system/'}

    experiment = Experiment()

    for cpu_type in cpu_types:
        for vector_length_multiple in vls:
            for benchmark_size in sizes:
                for n_software_threads in n_threads:
                    vector_length_multiple = str(vector_length_multiple)
                    n_software_threads = str(n_software_threads)
                    unit = generate_XSBench_experiment_unit(cpu_type, vector_length_multiple, benchmark_size, n_software_threads, env)
                    experiment.add_experiment_unit(unit)

    n_processes = len(experiment.experiment_units)
    experiment.launch(n_processes)
