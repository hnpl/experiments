from gem5.components.boards.riscv_board import RiscvBoard
from gem5.components.memory.memory import ChanneledMemory
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.utils.override import overrides
from gem5.resources.resource import Resource, CustomResource, DiskImageResource
from gem5.simulate.simulator import Simulator
from gem5.simulate.exit_event import ExitEvent

import m5
from m5.objects import DDR4_2400_16x4

from gem5_components.octopi_cache.Octopi import OctopiCache
from pathlib import Path

requires(isa_required=ISA.RISCV)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--command", type=str)
parser.add_argument("--checkpoint_path", type=str)
args = parser.parse_args()

num_ccxs = 1
num_cores = 8
command = args.command

cache_hierarchy = OctopiCache(
    l1i_size  = "32KiB",
    l1i_assoc = 8,
    l1d_size  = "32KiB",
    l1d_assoc = 8,
    l2_size  = "512KiB",
    l2_assoc = 8,
    l3_size = "32MiB",
    l3_assoc = 16,
    num_core_complexes = num_ccxs,
    use_dma_ports = True,
)

memory = ChanneledMemory(
    dram_interface_class = DDR4_2400_16x4,
    num_channels = 2,
    interleaving_size = 2**8,
    size = "16GiB",
    addr_mapping = None
)

processor = SimpleProcessor(
    cpu_type=CPUTypes.O3, isa=ISA.RISCV, num_cores=num_cores
)

class HighPerformanceRiscvBoard(RiscvBoard):
    @overrides(RiscvBoard)
    def get_default_kernel_args(self):
        return [
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "lpj=7999923",
            "root=/dev/vda1",
            "init=/root/gem5-init.sh",
            "rw",
        ]

# Setup the board.
board = HighPerformanceRiscvBoard(
    clk_freq="4GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the Full System workload.
board.set_kernel_disk_workload(
    kernel=Resource("riscv-bootloader-vmlinux-5.10"),
    disk_image=DiskImageResource("/scr/hn/DISK_IMAGES/rv64gc-hpc-2204.img"),
    readfile_contents=f"{command}",
    checkpoint=Path(args.checkpoint_path)
)

def save_checkpoint():
    simulator.save_checkpoint(args.checkpoint_path)

def handle_work_begin():
    print(f"Exit due to m5_work_begin()")
    print(f"info: Resetting stats")
    m5.stats.reset()
    #print(f"info: Switching CPU")
    #processor.switch()
    #save_checkpoint()
    yield False

def handle_work_end():
    print(f"Exit due to m5_work_end()")
    print(f"info: Dumping stats")
    m5.stats.dump()
    yield False

def handle_exit():
    print(f"Exit due to m5_exit()")
    yield True

simulator = Simulator(
    board=board,
    on_exit_event={
        ExitEvent.WORKBEGIN: handle_work_begin(), # save checkpoint here
        ExitEvent.WORKEND: handle_work_end(),
        ExitEvent.EXIT: handle_exit()
    }
)
print("Beginning simulation!")
simulator.run()
