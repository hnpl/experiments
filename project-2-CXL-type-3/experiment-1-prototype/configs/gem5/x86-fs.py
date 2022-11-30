from gem5.components.boards.x86_board import X86Board
from gem5.components.memory import SingleChannelDDR3_1600, SingleChannelDDR4_2400
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.processors.cpu_types import CPUTypes
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.resources.resource import Resource, CustomResource
from gem5.simulate.simulator import Simulator
from gem5.utils.override import overrides
from m5.objects import DDR4_2400_16x4, AddrRange, Addr, DDR3_1600_8x8, MemCtrl

# Run a check to ensure the right version of gem5 is being used.
requires(isa_required=ISA.X86)

# Setup the cache hierarchy.
# For classic, PrivateL1PrivateL2 and NoCache have been tested.
# For Ruby, MESI_Two_Level and MI_example have been tested.
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="32KiB", l1i_size="32KiB", l2_size="512KiB"
)

# Setup the system memory.
memory = SingleChannelDDR4_2400("1GiB")

# Setup a single core Processor.
processor = SimpleProcessor(
    cpu_type=CPUTypes.KVM, isa=ISA.X86, num_cores=1
)

class ModifiedX86Board(X86Board):
    @overrides(X86Board)
    def _pre_instantiate(self):
        self._connect_things()

        self.pool_memory = DDR3_1600_8x8(
            range=AddrRange(start=2**33, size=2**28),
        )
        self.pool_memory_mem_ctrl = MemCtrl(
            dram=self.pool_memory,
            port=self.cache_hierarchy.membus.mem_side_ports
        )

    @overrides(X86Board)
    def get_default_kernel_args(self):
        return [
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "lpj=7999923",
            "root=/dev/sda1",
            #"init=aaa",
            "rw",
        ]

# Setup the board.
board = ModifiedX86Board(
    clk_freq="1GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# Set the Full System workload.
board.set_kernel_disk_workload(
    kernel=CustomResource("/scr/hn/CXL/linux-x86/vmlinux"),
    disk_image=CustomResource("/scr/hn/CXL/ubuntu-cxl-x86.img"),
)

simulator = Simulator(board=board)
print("Beginning simulation!")
simulator.run()
