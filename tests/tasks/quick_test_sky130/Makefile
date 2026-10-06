# 
# Qsyn run Makefile
# =================
# Include the common setting and variables
include ../../common/qsyn_run_makefile_head.inc 
# All the targets below is visible through 'make help'

# Start your own targets here 
unzip_netlist:
# Uncompress golden netlist for synthesis
	tar -zxvf netlist.tar.gz

synth: unzip_netlist
# Run a flow to complete all the synthesis tasks defined in the configuration file
	${PYTHON_EXEC} ${SCRIPT_DIR}/run_qsyn_task.py --config ./config/qsyn_task.yaml --root_directory ${PROJ_HOME} --jobs ${NUM_JOBS}

generate_script_only: unzip_netlist
# Generate the input files required by synthesis flow. Users need to run synthesis manually
	${PYTHON_EXEC} ${SCRIPT_DIR}/run_qsyn_task.py --config ./config/qsyn_task.yaml --root_directory ${PROJ_HOME} ${OTHER_OPTIONS} --jobs ${NUM_JOBS}

clean:
# Remove all the previous run
	rm -rf ${QSYN_RUN_DIR}* reports/*

# All of your targets should be declared before the tail is included
# Include the common setting and variables
include ../../common/qsyn_run_makefile_tail.inc 

