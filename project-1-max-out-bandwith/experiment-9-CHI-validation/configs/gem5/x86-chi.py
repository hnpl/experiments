from gem5.components.boards.x86_board import X86Board
from gem5.components.boards.abstract_board import AbstractBoard
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

from saga.saga.cache_hierarchy import SagaCacheHierarchy

from pathlib import Path

requires(isa_required=ISA.X86)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--num_ccds", type=int, help="Number of cores", required=True)
parser.add_argument("--command", type=str, help="Command inputted to the guest system", required=True)
parser.add_argument("--enable_prefetcher", type=str, choices=["True", "False"], help="\"True\" if the prefetcher to L1 should be enable, \"False\" otherwise", required=True)
parser.add_argument("--num_channels", type=int, help="Number of memory channels", required=True)
args = parser.parse_args()

num_ccds = args.num_ccds
num_cores = 8 * num_ccds
command = args.command
enable_prefetcher = True if args.enable_prefetcher == "True" else False

cache_hierarchy = SagaCacheHierarchy()

memory = ChanneledMemory(
    dram_interface_class = DDR4_2400_16x4,
    num_channels = 2,
    interleaving_size = 2**8,
    size = "3GiB",
    addr_mapping = None
)

processor = SimpleSwitchableProcessor(
    starting_core_type = CPUTypes.KVM,
    switch_core_type = CPUTypes.TIMING,
    isa = ISA.X86,
    num_cores = num_cores,
)

class HighPerformanceX86Board(X86Board):
    def __init__(
        self, clk_freq, processor, memory, cache_hierarchy
    ):
        super().__init__(clk_freq, processor, memory, cache_hierarchy)

    @overrides(X86Board)
    def _pre_instantiate(self):
        super()._pre_instantiate()

    @overrides(X86Board)
    def get_default_kernel_args(self):
        return [
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "lpj=7999923",
            "root=/dev/sda1",
            "rw",
        ]

# Setup the board.
board = HighPerformanceX86Board(
    clk_freq="4GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the Full System workload.
board.set_kernel_disk_workload(
    kernel=CustomResource("/scr/hn/linux-5.15.119/vmlinux"),
    disk_image=DiskImageResource("/projects/gem5/hn/DISK_IMAGES/x86_64-hpc-2204.img"),
    readfile_contents=f"{command}",
)

def handle_work_begin():
    print(f"Exit due to m5_work_begin()")
    print(f"info: Resetting stats")
    m5.stats.reset()
    #print(f"info: Switching CPU")
    #processor.switch()
    yield False

def handle_work_end():
    print(f"Exit due to m5_work_end()")
    print(f"info: Dumping stats")
    m5.stats.dump()
    yield False

counter = 0

def handle_exit():
    global counter
    counter += 1
    print(f"Exit due to m5_exit()")
    if counter == 1:
        print(f"info: Switching CPU")
        processor.switch()
        yield False
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
