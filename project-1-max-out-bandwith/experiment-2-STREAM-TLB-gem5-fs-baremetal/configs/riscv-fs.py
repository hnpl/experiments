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
from gem5.resources.resource import Resource
from gem5.simulate.simulator import Simulator

import m5

import argparse

# Run a check to ensure the right version of gem5 is being used.
requires(isa_required=ISA.RISCV)

parser = argparse.ArgumentParser("RISC-V Unmatched board Full System simulation")
parser.add_argument("--disk_image_path", type=str, required=True, help="Path to the disk image")
parser.add_argument("--num_stream_array_elements", type=str, required=True, help="Number of elements in the STREAM arrays")
parser.add_argument("--num_cores", type=int, required=False, default=5, help="Number of U74 cores on the board, default: 5")
parser.add_argument("--num_tlb_entries", type=int, required=False, default=512, help="Number of TLB entries assuming TLB is a 1 level fully associative cache, default: 512")
args = parser.parse_args()

disk_image_path = args.disk_image_path
num_cores = args.num_cores
num_stream_array_elements = args.num_stream_array_elements
num_tlb_entries = args.num_tlb_entries

board = RISCVMatchedBoard(num_cores = num_cores, is_fs=True)
for core_idx in range(num_cores):
    board.processor.cores[core_idx].core.mmu.itb.size = num_tlb_entries
    board.processor.cores[core_idx].core.mmu.dtb.size = num_tlb_entries

# Set the Full System workload.
board.set_kernel_disk_workload(
    kernel=Resource("riscv-bootloader-vmlinux-5.10"),
    disk_image=CustomResource(f"{disk_image_path}"),
    readfile_contents=f"{num_stream_array_elements}"
)

simulator = Simulator(board=board)
print("Beginning simulation!")

# now: start
simulator.run()
# now: the beginning of the second iteration
m5.stats.reset()
print("Reset stats")
simulator.run()
# now: the end of the last iteration
m5.stats.dump()
print("Print results")
simulator.run()
