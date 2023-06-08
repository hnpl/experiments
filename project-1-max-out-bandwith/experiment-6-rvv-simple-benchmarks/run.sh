#!/bin/sh

mkdir results

gem5/build/RISCV/gem5.opt -re --outdir=results/stream_10000018_rv64gc riscv-simple-system-rvv.py --binary-path=/home/hn/simple-vectorizable-microbenchmarks/cpp/stream/stream_c.10000018 &
gem5/build/RISCV/gem5.opt -re --outdir=results/stream_10000018_rvv    riscv-simple-system-rvv.py --binary-path=/home/hn/simple-vectorizable-microbenchmarks/cpp/stream/stream_c.10000018.rvv &

gem5/build/RISCV/gem5.opt -re --outdir=results/gather_10000018_rv64gc riscv-simple-system-rvv.py --binary-path=/home/hn/simple-vectorizable-microbenchmarks/cpp/gather_load.riscv &
gem5/build/RISCV/gem5.opt -re --outdir=results/gather_10000018_rvv    riscv-simple-system-rvv.py --binary-path=/home/hn/simple-vectorizable-microbenchmarks/cpp/gather_load.rvv &

gem5/build/RISCV/gem5.opt -re --outdir=results/scatter_10000018_rv64gc riscv-simple-system-rvv.py --binary-path=/home/hn/simple-vectorizable-microbenchmarks/cpp/scatter_store.riscv &
gem5/build/RISCV/gem5.opt -re --outdir=results/scatter_10000018_rvv    riscv-simple-system-rvv.py --binary-path=/home/hn/simple-vectorizable-microbenchmarks/cpp/scatter_store.rvv &
