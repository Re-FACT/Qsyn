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
	${PYTHON_EXEC} ${SCRIPT_DIR}/run_qsyn_task.py --config ./config/qsyn_task.yaml  --tool_config ${TOOL_CONFIG_DIR}/syn_tool_config.yml --pdk_config ${PDK_CONFIG_DIR}/sky130_hd_constants.xml --root_directory ${PROJ_HOME} --qsyn_rundir ${QSYN_RUN_DIR} --jobs ${NUM_JOBS}

generate_script_only: unzip_netlist
# Generate the input files required by synthesis flow. Users need to run synthesis manually
	${PYTHON_EXEC} ${SCRIPT_DIR}/run_qsyn_task.py --config ./config/qsyn_task.yaml --tool_config ${TOOL_CONFIG_DIR}/syn_tool_config.yml --pdk_config ${PDK_CONFIG_DIR}/sky130_hd_constants.xml --root_directory ${PROJ_HOME} ${OTHER_OPTIONS}  --qsyn_rundir ${QSYN_RUN_DIR}--jobs ${NUM_JOBS}

parse_report:
# Generate area reports based on synthesis results. Users need to run synthesis manually
	${PYTHON_EXEC} ${SCRIPT_DIR}/run_qsyn_task.py --config ./config/qsyn_task.yaml --tool_config ${TOOL_CONFIG_DIR}/syn_tool_config.yml --pdk_config ${PDK_CONFIG_DIR}/sky130_hd_constants.xml --root_directory ${PROJ_HOME} ${OTHER_OPTIONS} --qsyn_rundir ${QSYN_RUN_DIR} --jobs ${NUM_JOBS} --parse_report_only --report_summary reports/post_synth_area.csv


clean:
# Remove all the previous run
	rm -rf ${QSYN_RUN_DIR}* reports/*

# All of your targets should be declared before the tail is included
# Include the common setting and variables
include ../../common/qsyn_run_makefile_tail.inc 

