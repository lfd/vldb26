#!/bin/bash

if [ ! "${PWD}" = "/home/repro/vldb26-repro" ]; then
    cd /home/repro/vldb26-repro/
fi

cd base

echo "Started running conventional MILP benchmarks..."

# run conventional experiments
python3 HybridMILPConvBenchmarks.py

echo "Started running scalability MILP benchmarks..."

# run scalability experiments
python3 HybridMILPScalabilityBenchmarks.py

echo "Started running adaptive optimisation step..."

cd Adaptive/queries

make

cd ../../

python3 HybridMILPScalabilityBenchmarksPostprocessing.py