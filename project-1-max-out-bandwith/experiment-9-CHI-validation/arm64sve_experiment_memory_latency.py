from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path
import subprocess
import multiprocessing

from gem5_components.workloads_params.memory_latency_params import MemoryLatencyTestParams
from gem5_components.workloads_params.isa_extensions import ISAExtension

from arm64sve_design_space import ARM64SVE_Design_Space

experiment_tag = "arm64sve-chi-validation-memory-latency"
gem5_binary_path = "/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast"
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-9-CHI-validation/configs/gem5/arm64sve-chi.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-9-CHI-validation/results/" + experiment_tag + "/"
disk_image_path = "/projects/gem5/hn/DISK_IMAGES/arm64sve-hpc-2204-20230526.img"

# the gem5 binary @ azacca in /scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast
# the gem5 repo is at https://github.com/takekoputa/gem5
# this binary is compiled off the develop branch
gem5_binary_md5sum = "7431a465f527fdb001de1a38039df55b"
disk_image_md5sum = "da7fde7a70e2ef0d7f9656793242df1d"

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())
    assert(Path(disk_image_path).exists())

def output_folder_generator(isa, workload_naming_string, vlen, num_ccds, enable_prefetcher, num_channels):
    return "-".join([isa, workload_naming_string, str(vlen), str(num_ccds), str(enable_prefetcher), str(num_channels)])

def gem5_params_generator(output_path, command, vlen, num_ccds, enable_prefetcher, num_channels):
    gem5_params = {}
    config_params = {}

    """
    gem5/build/RISCV_MESI_Three_Level/gem5.fast configs/gem5/arm64sve.py \
        --command "stream.hw 1000000" --num_ccds=1 --enable_prefetcher=False --num_channels=2 --vlen=512
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--command"] = command
    config_params["--vlen"] = vlen
    config_params["--num_ccds"] = num_ccds
    config_params["--enable_prefetcher"] = enable_prefetcher
    config_params["--num_channels"] = num_channels

    return gem5_params, config_params

def metadata_generator(isa, disk_image_path, command, workload_naming_string, vlen, num_ccds, enable_prefetcher, num_channels):
    metadata = {}

    metadata["tag"] = experiment_tag
    metadata["git-hash"] = "08644a76707ac8ee14f9ff0d52af7c3e324209f0"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "develop"

    metadata["gem5-binary-md5sum"] = gem5_binary_md5sum
    metadata["disk-image-md5sum"] = disk_image_md5sum

    metadata["isa"] = isa
    metadata["command"] = command
    metadata["disk-image-path"] = disk_image_path
    metadata["workload-naming-string"] = workload_naming_string
    metadata["more-details"] = "Saga cache"
    metadata["isa-string"] = "arm64sve"

    metadata["vlen"] = str(vlen)
    metadata["num_ccds"] = str(num_ccds)
    metadata["enable_prefetcher"] = str(enable_prefetcher)
    metadata["num_channels"] = str(num_channels)

    return metadata

def generate_experiment_unit(isa, vlen, num_ccds, enable_prefetcher, num_channels, params):
    workload_command = params.get_command()
    workload_naming_string = params.get_naming_string()

    output_folder_name = output_folder_generator(isa = isa,
                                                 workload_naming_string = workload_naming_string,
                                                 vlen = vlen,
                                                 num_ccds = num_ccds,
                                                 enable_prefetcher = enable_prefetcher,
                                                 num_channels = num_channels)

    output_path = str(Path(gem5_output_path_prefix) / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path = output_path,
                                                       command = workload_command,
                                                       vlen = vlen,
                                                       num_ccds = num_ccds,
                                                       enable_prefetcher = enable_prefetcher,
                                                       num_channels = num_channels)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = {})

    metadata = metadata_generator(isa = isa,
                                  disk_image_path = disk_image_path,
                                  command = workload_command,
                                  workload_naming_string = workload_naming_string,
                                  vlen = vlen,
                                  num_ccds = num_ccds,
                                  enable_prefetcher = enable_prefetcher,
                                  num_channels = num_channels)

    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    Path(gem5_output_path_prefix).mkdir(parents=True, exist_ok=True)

    sanity_check()

    experiment = Experiment()

    for vlen in ARM64SVE_Design_Space.vlen:
        for num_ccds in [1]: # only use 1 core
            for enable_prefetcher in ARM64SVE_Design_Space.enable_prefetcher:
                for num_channels in ARM64SVE_Design_Space.num_channels:
                    unit = generate_experiment_unit(
                        isa = "arm64sve",
                        vlen = str(vlen),
                        num_ccds = str(num_ccds),
                        enable_prefetcher = str(enable_prefetcher),
                        num_channels = str(num_channels),
                        params = MemoryLatencyTestParams(source_path=Path("/home/ubuntu/MemoryLatencyTest/"),
                                                         with_roi_annotations=True,
                                                         isa_extensions = [ISAExtension.SVE]))
                    experiment.add_experiment_unit(unit)

    n_processes = experiment.get_number_of_experiment_units()
    experiment.launch(n_processes)
