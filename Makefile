# Convenience targets. Everything also works by hand, see README.md
.PHONY: check sim all compare sweep maps clean

check:            ## can the robot turn in the corridor?
	python3 tools/geometry_check.py

maps:             ## regenerate the .txt maps from build_maps.py
	cd sim/maps && python3 build_maps.py

sim:              ## one run on the island-loop map, makes a GIF
	cd sim && python3 run.py --map maps/map3_loop.txt --scale 1.17

all:              ## every map, recommended settings, makes GIFs
	cd sim && python3 run.py --all --scale 1.17

compare:          ## every map x every strategy, no GIFs
	cd sim && python3 run.py --all --compare --no-gif --scale 1.17

sweep:            ## how narrow can the passages be?
	cd sim && python3 run.py --all --sweep-corridor --no-gif

clean:
	rm -f sim/libnavcore.so sim/*.dll sim/*.dylib
	rm -rf sim/__pycache__ sim/runs/*.csv
