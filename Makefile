# Convenience targets. Everything also works by hand, see README.md
.PHONY: check sim all compare sweep maps clean

check:            ## can the robot turn in the corridor?
	python3 tools/geometry_check.py

maps:             ## regenerate the .txt maps from build_maps.py
	cd sim/maps && python3 build_maps.py

sim:              ## one run on map 2, the one with the crossing, makes a GIF
	cd sim && python3 run.py --map maps/map2.txt

all:              ## every map, recommended settings, makes GIFs
	cd sim && python3 run.py --all

compare:          ## every map x every strategy, no GIFs
	cd sim && python3 run.py --all --compare --no-gif --trials 8

sweep:            ## how narrow can the passages be?
	cd sim && python3 run.py --all --sweep-corridor --no-gif

clean:
	rm -f sim/libnavcore.so sim/*.dll sim/*.dylib
	rm -rf sim/__pycache__ sim/runs/*.csv
