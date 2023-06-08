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

from gem5.resources.resource import Resource, CustomResource
from python.gem5.prebuilt.riscvmatched.riscvmatched_board import (
    RISCVMatchedBoard,
)
from gem5.isas import ISA
from gem5.utils.requires import requires
from gem5.utils.override import overrides
from gem5.resources.resource import Resource
from gem5.simulate.simulator import Simulator

import m5

import argparse

# Run a check to ensure the right version of gem5 is being used.
requires(isa_required=ISA.RISCV)

parser = argparse.ArgumentParser("RISC-V Unmatched board Full System simulation")
parser.add_argument("--path", type=str, required=True, help="Path to the binary")
parser.add_argument("--mshrs", type=int, required=True, help="Number of Miss Status Holding Registers")
args = parser.parse_args()

class ModifiedRISCVMatchedBoard(RISCVMatchedBoard):
    def __init__(self, num_cores = 0, clk_freq = "1.2GHz", l2_size = "2MiB", is_fs = False):
        super().__init__(num_cores, clk_freq, l2_size, is_fs)

    @overrides(RISCVMatchedBoard)
    def _pre_instantiate(self):
        self._connect_things()
        for core_idx in range(self.processor.get_num_cores()):
            self.cache_hierarchy.dptw_caches[core_idx].mshrs = args.mshrs
            self.cache_hierarchy.iptw_caches[core_idx].mshrs = args.mshrs
            self.cache_hierarchy.l1dcaches[core_idx].mshrs = args.mshrs
            self.cache_hierarchy.l1icaches[core_idx].mshrs = args.mshrs
            self.cache_hierarchy.l2caches[core_idx].mshrs = args.mshrs

    @overrides(RISCVMatchedBoard)
    def get_default_kernel_args(self):
        return [
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "lpj=7999923",
            "root=/dev/vda1",
            "init=/root/init.sh",
            "rw",
        ]

board = ModifiedRISCVMatchedBoard(num_cores=1, is_fs=False)

# Set the Full System workload.
board.set_se_binary_workload(CustomResource(args.path))

simulator = Simulator(board=board)
print("Beginning simulation!")

# now: start
simulator.run()
