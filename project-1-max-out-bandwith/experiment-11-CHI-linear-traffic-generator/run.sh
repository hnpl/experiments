#!/bin/bash

/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast -re --outdir=results/1ccd_1ms configs/gem5/linear-traffic.py --num_cores=8 --duration=1ms &
/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast -re --outdir=results/1ccd_10ms configs/gem5/linear-traffic.py --num_cores=8 --duration=10ms &
/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast -re --outdir=results/1ccd_100ms configs/gem5/linear-traffic.py --num_cores=8 --duration=100ms &
/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast -re --outdir=results/2ccds_1ms configs/gem5/linear-traffic.py --num_cores=16 --duration=1ms &
/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast -re --outdir=results/2ccds_10ms configs/gem5/linear-traffic.py --num_cores=16 --duration=10ms &
/scr/hn/takekoputa-gem5/build/ARM_CHI/gem5.fast -re --outdir=results/2ccds_100ms configs/gem5/linear-traffic.py --num_cores=16 --duration=100ms &
