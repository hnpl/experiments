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
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-5-EPYC-like-system/configs/gem5/rv64gc-1ccd-2channel-atomic-timing.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-5-EPYC-like-system/results/" + experiment_tag + "/"
disk_image_path = "/scr/hn/DISK_IMAGES/rv64gc-hpc-2204.img"

# the gem5 binary @ azacca in /scr/hn/gem5-takekoputa-stream/build/RISCV_MESI_Three_Level/gem5.fast
# the gem5 repo is at https://github.com/takekoputa/gem5
# this binary is compiled off the rvv branch
gem5_binary_md5sum = "3361e5972b9bf006ac864a31748c194d"
disk_image_md5sum = "01ad7ff5586d1970c5d78f40086380fa"

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
    metadata["git-hash"] = "f9cf3de711d59bc3a81bb8d49f1408b1f6349a7b(gem5)+44910a688f61d2d953868af0fa5dee2349ebbecbmine)"
    metadata["git-remote"] = "https://github.com/takekoputa/gem5"
    metadata["git-branch"] = "rvv"

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

    # Adding some GUPS workloads
    table_number_of_elements = [2**10]
    inner_loop_number_of_elements = 128
    for size in table_number_of_elements:
        unit = generate_experiment_unit(isa = "riscv",
                                        params = GUPSParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/gups/"),
                                                            with_roi_annotations=True,
                                                            table_number_of_elements=size,
                                                            number_of_updates_inner_loop=inner_loop_number_of_elements))
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
