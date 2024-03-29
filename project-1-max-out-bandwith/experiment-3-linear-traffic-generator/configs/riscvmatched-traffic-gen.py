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

from gem5.simulate.simulator import Simulator
from gem5.utils.override import overrides
from gem5.utils.requires import requires

from gem5.components.boards.test_board import TestBoard
from gem5.components.processors.linear_generator import LinearGenerator
from gem5.components.processors.random_generator import RandomGenerator

from gem5.prebuilt.riscvmatched import riscvmatched_board, riscvmatched_cache

parser = argparse.ArgumentParser("RISC-V Unmatched board with traffic generators")
parser.add_argument("--num_cores", type=int, required=False, default=4, help="Number of traffic generators, default: 4")
args = parser.parse_args()

num_cores = args.num_cores

linear_traffic_generator = LinearGenerator(
    num_cores=num_cores, duration="1s", rate="32GiB/s", max_addr=2**34, rd_perc=50
)

class ModifiedTestBoard(TestBoard):
    def __init__(self, clk_freq, generator, memory, cache_hierarchy):
        super().__init__(clk_freq, generator, memory, cache_hierarchy)
    @overrides(TestBoard)
    def _pre_instantiate(self):
        self._connect_things()
        for core_idx in range(self.processor.get_num_cores()):
            self.cache_hierarchy.dptw_caches[core_idx].mshrs = 1
            self.cache_hierarchy.iptw_caches[core_idx].mshrs = 1
            self.cache_hierarchy.l1dcaches[core_idx].mshrs = 1
            self.cache_hierarchy.l1icaches[core_idx].mshrs = 1
            self.cache_hierarchy.l2caches[core_idx].mshrs = 1
            self.cache_hierarchy.l2buses[core_idx].snoop_filter.max_capacity = "100MiB"
        self.cache_hierarchy.membus.snoop_filter.max_capacity = "100MiB"

board = ModifiedTestBoard(clk_freq="1GHz",
                          generator=linear_traffic_generator,
                          memory=riscvmatched_board.U74Memory(),
                          cache_hierarchy=riscvmatched_cache.RISCVMatchedCacheHierarchy(l2_size="2MiB"))

simulator = Simulator(board=board, full_system=False)
simulator.run()

