SHELL = bash
PYTHON_EXEC ?= python3
QSYN_RUN_DIR = _qsyn
SCRIPT_DIR = ../../../scripts
PROJ_HOME = ../../../
OTHER_OPTIONS = --file_generation_only
NUM_JOBS = 2

.SILENT:

# Put it first so that "make" without argument is like "make help".
export COMMENT_EXTRACT
help:
	@${PYTHON_EXEC} -c "$$COMMENT_EXTRACT"
