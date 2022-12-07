from gem5.components.boards.riscv_board import RiscvBoard
from gem5.components.memory.memory import ChanneledMemory
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.utils.override import overrides
from gem5.resources.resource import Resource, CustomResource
from gem5.simulate.simulator import Simulator

from m5.objects import HBM_1000_4H_1x64

from components.TLDR import TLDRCache

requires(isa_required=ISA.RISCV)

cache_hierarchy = TLDRCache(
    l1i_size  = "32KiB",
    l1i_assoc = 8,
    l1d_size  = "32KiB",
    l1d_assoc = 8,
    l2_size  = "512KiB",
    l2_assoc = 8,
    l3_size = "32MiB",
    l3_assoc = 32,
    num_core_complexes = 2,
)

memory = ChanneledMemory(
    dram_interface_class = HBM_1000_4H_1x64,
    num_channels = 2, # should equal to the number of core complexes
    interleaving_size = 2**8,
    size = "8GiB",
    addr_mapping = None
)

processor = SimpleProcessor(
    cpu_type=CPUTypes.TIMING, isa=ISA.RISCV, num_cores=16
)

class HighPerformanceRiscvBoard(RiscvBoard):
    @overrides(RiscvBoard)
    def get_default_kernel_args(self):
        return [
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "lpj=7999923",
            "root=/dev/vda1",
            "init=/root/init.sh",
            "rw",
        ]

# Setup the board.
board = HighPerformanceRiscvBoard(
    clk_freq="4GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("command", type=str)
args = parser.parse_args()

command = args.command

# Set the Full System workload.
board.set_kernel_disk_workload(
    kernel=Resource("riscv-bootloader-vmlinux-5.10"),
    disk_image=CustomResource("/scr/hn/DISK_IMAGES/ubuntu-hpc-riscv.img"),
    readfile_contents=f"{command}"
)

simulator = Simulator(board=board)
print("Beginning simulation!")
simulator.run()
