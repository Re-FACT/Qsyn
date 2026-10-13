SHELL = bash
PYTHON_EXEC ?= python3
QSYN_RUN_DIR = _work/_qsyn
SCRIPT_DIR = ../../../scripts
TOOL_CONFIG_DIR = ../../../etc/tool_config
PDK_CONFIG_DIR = ../../../etc/pdk_config
PROJ_HOME = ../../../
OTHER_OPTIONS = --file_generation_only
NUM_JOBS = 2

.SILENT:

# Put it first so that "make" without argument is like "make help".
export COMMENT_EXTRACT
help:
	@${PYTHON_EXEC} -c "$$COMMENT_EXTRACT"
