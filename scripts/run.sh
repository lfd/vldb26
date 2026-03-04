#!/bin/bash

if [ $# -eq 0 ]; then
	echo "Usage: ./scripts/run.sh [all|bash]"
	exit 1
fi

if [ ! "${PWD}" = "/home/repro/vldb26-repro" ]; then
    cd /home/repro/vldb26-repro/
fi

cd scripts/

if [ "$1" = "all" ]; then
	./run_all.sh
elif [ "$1" = "bash" ]; then
	# launch shell
	cd ..
	/bin/bash
	exit 0
else
    echo "Usage: ./scripts/run.sh [all|bash]"
fi

cd ..

# launch shell
/bin/bash