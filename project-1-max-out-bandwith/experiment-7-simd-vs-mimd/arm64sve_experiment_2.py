from gem5_launch_utils.Experiment import Experiment
from gem5_launch_utils.ExperimentUnit import ExperimentUnit

from pathlib import Path
import subprocess
import multiprocessing

from gem5_components.workloads_params.npb_params import NPBParams, NPBBenchmark, NPBClass
from gem5_components.workloads_params.spatter_params import SpatterParams
from gem5_components.workloads_params.gups_params import GUPSParams
from gem5_components.workloads_params.stream_params import STREAMParams
from gem5_components.workloads_params.permutating_gather import PermutatingGatherParams
from gem5_components.workloads_params.permutating_scatter import PermutatingScatterParams
from gem5_components.workloads_params.isa_extensions import ISAExtension

experiment_tag = "arm64sve-simd-mimd-2"
gem5_binary_path = "/home/hn/takekoputa-gem5/build/ARM_MESI_Three_Level/gem5.fast"
gem5_config_path = "/home/hn/experiments/project-1-max-out-bandwith/experiment-7-simd-vs-mimd/configs/gem5/arm64sve-1ccd-2channel-prefetcher.py"
gem5_output_path_prefix = "/home/hn/experiments/project-1-max-out-bandwith/experiment-7-simd-vs-mimd/results/" + experiment_tag + "/"
disk_image_path = "/projects/gem5/hn/DISK_IMAGES/arm64sve-hpc-2204.img"

# the gem5 binary @ azacca in /scr/hn/gem5-takekoputa-stream/build/ARM_MESI_Three_Level/gem5.fast
# the gem5 repo is at https://github.com/takekoputa/gem5
# this binary is compiled off the rvv-change-69897 branch
gem5_binary_md5sum = "3718623d0470c82a7c35b6723009be71"
disk_image_md5sum = "8891cda46cb77e7b795ee49eb060aa72"

def sanity_check():
    assert(Path(gem5_binary_path).exists())
    assert(Path(gem5_output_path_prefix).exists())
    assert(Path(disk_image_path).exists())

def output_folder_generator(isa, workload_naming_string, num_cores, vlen):
    return "-".join([isa, workload_naming_string, str(num_cores), str(vlen)])

def gem5_params_generator(output_path, command, num_cores, vlen):
    gem5_params = {}
    config_params = {}

    """
    gem5/build/RISCV_MESI_Three_Level/gem5.fast configs/gem5/arm64sve-1ccd-2channel.py \
        --command "/home/ubuntu/NPB/NPB3.4-OMP/bin/cg.A.x"  --num_core=16 --vlen=128
    """
    # parameters for redirecting results
    gem5_params["-re"] = ""
    gem5_params["--outdir"] = output_path
    gem5_params["--listener-mode=off"] = ""

    config_params["--command"] = command
    config_params["--num_cores"] = num_cores
    config_params["--vlen"] = vlen

    return gem5_params, config_params

def metadata_generator(isa, disk_image_path, command, workload_naming_string, num_cores, vlen):
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
    metadata["more-details"] = "Octopi cache with 1 ccd, 2-channeled memory, O3 CPU"
    metadata["isa-string"] = "arm64sve"
    metadata["num-cores"] = str(num_cores)
    metadata["vlen"] = str(vlen)

    return metadata

def generate_experiment_unit(isa, num_cores, vlen, params):
    workload_command = params.get_command()
    workload_naming_string = params.get_naming_string()

    output_folder_name = output_folder_generator(isa, workload_naming_string, num_cores, vlen)
    output_path = str(Path(gem5_output_path_prefix) / output_folder_name)

    gem5_params, config_params = gem5_params_generator(output_path, workload_command, num_cores, vlen)

    unit = ExperimentUnit(gem5_binary_path = gem5_binary_path,
                          gem5_config_path = gem5_config_path,
                          gem5_output_path = output_path,
                          gem5_params = gem5_params,
                          config_params = config_params,
                          env = {})

    metadata = metadata_generator(isa, disk_image_path, workload_command, workload_naming_string, num_cores, vlen)
    for key, val in metadata.items():
        unit.add_metadata(key, val)

    return unit

if __name__ == "__main__":
    Path(gem5_output_path_prefix).mkdir(parents=True, exist_ok=True)

    sanity_check()

    experiment = Experiment()

    num_cores_vlen_product = 2048

    for num_cores in [1, 2, 4, 8, 16]:
        vlen = num_cores_vlen_product // num_cores

        # Adding some spatter workloads
        for json_file in ["/home/ubuntu/lanl-spatter/patterns/flag/static_2d/001.json",
                          "/home/ubuntu/lanl-spatter/patterns/flag/static_2d/001.nonfp.json",
                          "/home/ubuntu/lanl-spatter/patterns/flag/static_2d/001.fp.json",
                          "/home/ubuntu/lanl-spatter/patterns/xrage/asteroid/spatter.json",
                          ]:
            unit = generate_experiment_unit(isa = "arm64sve",
                                            num_cores = str(num_cores),
                                            vlen = str(vlen),
                                            params = SpatterParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/spatter/"),
                                                                   with_roi_annotations=True,
                                                                   json_filepath=json_file,
                                                                   isa_extensions = [ISAExtension.SVE]))
            experiment.add_experiment_unit(unit)


        # Adding some STREAM workloads
        stream_sizes = [2**k for k in range(24, 27)] + [2**k + 2**(k-1) for k in range(24, 26)] # somewhere between 2**27 bytes and 2**30 bytes
        for stream_size in stream_sizes:
            unit = generate_experiment_unit(isa = "arm64sve",
                                            num_cores = str(num_cores),
                                            vlen = str(vlen),
                                            params = STREAMParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/stream/"),
                                                                  with_roi_annotations=True,
                                                                  number_of_elements=stream_size,
                                                                  isa_extensions = [ISAExtension.SVE]))
            experiment.add_experiment_unit(unit)

        # Permutating gather workload
        unit = generate_experiment_unit(isa = "arm64sve",
                                        num_cores = str(num_cores),
                                        vlen = str(vlen),
                                        params = PermutatingGatherParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/permutating_gather/"),
                                                                         with_roi_annotations=True,
                                                                         seed=17,
                                                                         mod=100_000_007,
                                                                         isa_extensions = [ISAExtension.SVE]))
        experiment.add_experiment_unit(unit)

        # Permutating scatter workload
        unit = generate_experiment_unit(isa = "arm64sve",
                                        num_cores = str(num_cores),
                                        vlen = str(vlen),
                                        params = PermutatingScatterParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/permutating_scatter/"),
                                                                          with_roi_annotations=True,
                                                                          seed=17,
                                                                          mod=100_000_007,
                                                                          isa_extensions = [ISAExtension.SVE]))
        experiment.add_experiment_unit(unit)

        # Adding some GUPS workloads
        table_number_of_elements = [2**k for k in range(20, 23)]
        inner_loop_number_of_elements = 128
        for size in table_number_of_elements:
            unit = generate_experiment_unit(isa = "arm64sve",
                                            num_cores = str(num_cores),
                                            vlen = str(vlen),
                                            params = GUPSParams(source_path=Path("/home/ubuntu/simple-vectorizable-microbenchmarks/gups/"),
                                                                with_roi_annotations=True,
                                                                table_number_of_elements=size,
                                                                number_of_updates_inner_loop=inner_loop_number_of_elements,
                                                                isa_extensions = [ISAExtension.SVE]))
            experiment.add_experiment_unit(unit)

    n_processes = 60
    experiment.launch(n_processes)
