# Copyright (c) 2022 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse

from gem5.resources.resource import Resource, CustomResource
from gem5.simulate.simulator import Simulator
from python.gem5.prebuilt.riscvmatched.riscvmatched_board import (
    RISCVMatchedBoard,
)
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.utils.override import overrides

import m5

requires(isa_required=ISA.RISCV)

parser = argparse.ArgumentParser("RISC-V Unmatched board")
parser.add_argument("--binary", type=str, required=True, help="Path to the binary")
parser.add_argument("--num_cores", type=int, required=False, default=5, help="Number of U74 cores on the board, default: 5")
args = parser.parse_args()

num_cores = args.num_cores

class ModifiedRISCVMatchedBoard(RISCVMatchedBoard):
    def __init__(self, num_cores = 0, clk_freq = "1.2GHz", l2_size = "2MiB", is_fs = False):
        super().__init__(num_cores, clk_freq, l2_size, is_fs)
    @overrides(RISCVMatchedBoard)
    def _pre_instantiate(self):
        self._connect_things()
        for core_idx in range(self.processor.get_num_cores()):
            board.cache_hierarchy.dptw_caches[core_idx].mshrs = 1
            board.cache_hierarchy.iptw_caches[core_idx].mshrs = 1
            board.cache_hierarchy.l1dcaches[core_idx].mshrs = 1
            board.cache_hierarchy.l1icaches[core_idx].mshrs = 1
            board.cache_hierarchy.l2caches[core_idx].mshrs = 1

board = ModifiedRISCVMatchedBoard(num_cores = num_cores)

board.set_se_binary_workload(CustomResource(args.binary))

simulator = Simulator(board=board, full_system=False)

# Warm up
simulator.run()

# ROI
print("Reset stats")
m5.stats.reset()
print("Begin the second iteration")
simulator.run()
m5.stats.dump()
print("Done the second iteration")

# Report bandwidth
simulator.run()
