#!/bin/sh

ln -s ../../gem5_launch_utils gem5_launch_utils 

git clone https://github.com/takekoputa/gem5_components

mkdir -p configs/gem5
cd configs/gem5
git clone https://github.com/takekoputa/gem5_components # yeah, we are doing it twice

