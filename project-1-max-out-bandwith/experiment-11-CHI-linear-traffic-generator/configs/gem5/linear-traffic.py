# Copyright (c) 2023 The Regents of the University of California
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
from gem5.components.memory.memory import ChanneledMemory

from saga.saga.cache_hierarchy import SagaCacheHierarchy
from m5.objects import DDR4_2400_16x4

parser = argparse.ArgumentParser()
parser.add_argument("--num_cores", type=int)
parser.add_argument("--duration", type=str)
args = parser.parse_args()
num_cores = args.num_cores
duration = args.duration

linear_traffic_generator = LinearGenerator(
    num_cores=num_cores, duration=duration, rate="32GiB/s", min_addr=2**31, max_addr=2**34, rd_perc=50
)

board = TestBoard(
    clk_freq="4GHz",
    generator=linear_traffic_generator,
    memory=ChanneledMemory(
        dram_interface_class = DDR4_2400_16x4,
        num_channels = 2,
        interleaving_size = 2**8,
        size = "16GiB",
        addr_mapping = None
    ),
    cache_hierarchy=SagaCacheHierarchy())

simulator = Simulator(board=board, full_system=False)
simulator.run()

