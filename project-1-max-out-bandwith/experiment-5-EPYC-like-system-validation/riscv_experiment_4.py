from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path
import subprocess
import multiprocessing

from gem5_components.workloads_params.npb_params import NPBParams, NPBBenchmark, NPBClass
from gem5_components.workloads_params.spatter_params import SpatterParams
from gem5_components.workloads_params.gups_params import GUPSParams

experiment_tag = "riscv-hpc-test-4"
gem5_binary_path = "/scr/hn/takekoputa-gem5/build/RISCV_MESI_Three_Level/gem5.fast"
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-5-EPYC-like-system-validation/configs/gem5/rv64gc-1ccd-2channel-atomic-timing.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-5-EPYC-like-system-validation/results/" + experiment_tag + "/"
disk_image_path = "/scr/hn/DISK_IMAGES/rv64gc-hpc-2204.img"

# the gem5 binary @ azacca in /scr/hn/gem5-takekoputa-stream/build/RISCV_MESI_Three_Level/gem5.fast
# the gem5 repo is at https://github.com/takekoputa/gem5
# this binary is compiled off the rvv-change-69897 branch
gem5_binary_md5sum = "89f75454c7b84663a6569cb5979bcb64"
disk_image_md5sum = "29c93cb76d41aa7081adf195ad70797d"

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())
    assert(Path(disk_image_path).exists())

def output_folder_generator(isa, workload_naming_string):
    return "-".join([isa, workload_naming_string])

def gem5_params_generator(output_path, command):
    gem5_params = {}
    config_params = {}

    """
    gem5/build/RISCV_MESI_Three_Level/gem5.fast configs/gem5/rv64gc-1ccd-2channel.py \
        --command "/home/ubuntu/NPB/NPB3.4-OMP/bin/cg.A.x"
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--command"] = command

    return gem5_params, config_params

def metadata_generator(isa, disk_image_path, command, workload_naming_string):
    metadata = {}

    metadata["tag"] = experiment_tag
    metadata["git-hash"] = "851e469e55b69533a36de634bd1d1f424b31b07e(gem5)+" \
                           "65ab68d46037b574f5982649c3175152d61594e3(cherry-pick)+" \
                           "8fb0dee86aa84fa13bccb40ce31513ead030b3ac(mine)"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "rvv-change-69897"

    metadata["gem5-binary-md5sum"] = gem5_binary_md5sum
    metadata["disk-image-md5sum"] = disk_image_md5sum

    metadata["isa"] = isa
    metadata["command"] = command
    metadata["disk-image-path"] = disk_image_path
    metadata["workload-naming-string"] = workload_naming_string
    metadata["more-details"] = "Octopi cache with 1 ccd, 2-channeled memory, atomic switching to timing cpu"
    metadata["isa-string"] = "rv64gc"

    return metadata

def generate_experiment_unit(isa, params):
    workload_command = params.get_command()
    workload_naming_string = params.get_naming_string()

    output_folder_name = output_folder_generator(isa, workload_naming_string)
    output_path = str(Path(gem5_output_path_prefix) / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path, workload_command)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = {})

    metadata = metadata_generator(isa, disk_image_path, workload_command, workload_naming_string)
    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    Path(gem5_output_path_prefix).mkdir(parents=True, exist_ok=True)

    sanity_check()

    experiment = Experiment()

    # Adding some spatter workloads
    for json_file in ["/home/ubuntu/lanl-spatter/patterns/flag/static_2d/001.json",
                      ]:
        unit = generate_experiment_unit(isa = "riscv",
                                        params = SpatterParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/spatter/"),
                                                               with_roi_annotations=True,
                                                               json_filepath=json_file))
        experiment.add_experiment_unit(unit)

    # Adding some NPB workloads
    for npb_workload in [NPBBenchmark.BT, NPBBenchmark.CG, NPBBenchmark.FT, NPBBenchmark.IS, NPBBenchmark.LU, NPBBenchmark.MG, NPBBenchmark.SP, NPBBenchmark.UA]:
        for npb_workload_class in [NPBClass.S]:
            unit = generate_experiment_unit(isa = "riscv",
                                            params = NPBParams(source_path=Path("/home/ubuntu/NPB/"),
                                                               with_roi_annotations=True,
                                                               benchmark=npb_workload,
                                                               size=npb_workload_class))
            experiment.add_experiment_unit(unit)


    n_processes = 10
    experiment.launch(n_processes)
