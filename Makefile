# Makefile
SHELL=bash
PYTHON_EXEC=python3
VERSION_FILE = VERSION.md
TAGGED_COMMIT_FILE = .TAGGED_COMMIT
VERSION_BUMP_TYPE = minor
FORCE_COMMIT_VERSION_UPDATE = off
INFRA_ROOT = /eda/internal/alkaid_infra/
NUM_JOBS = 2

# Format executables
PYTHON_FORMAT_EXEC ?= black

.SILENT:

# Put it first so that "make" without argument is like "make help".
export COMMENT_EXTRACT

# Put it first so that "make" without argument is like "make help".
help:
	@${PYTHON_EXEC} -c "$$COMMENT_EXTRACT"

update_version:
# Update the patch count in the version number
	echo "======== Bump up patch count in the version number ========"; \
	${PYTHON_EXEC} ${INFRA_ROOT}/scripts/version_updater.py --version_file ${VERSION_FILE} --tagged_commit ${TAGGED_COMMIT_FILE} --force_commit ${FORCE_COMMIT_VERSION_UPDATE}	

release_version:
# Update the patch count in the version number
	echo "======== Bump up release in the version number ========"; \
	${PYTHON_EXEC} ${INFRA_ROOT}/scripts/version_updater.py --version_file ${VERSION_FILE} --tagged_commit ${TAGGED_COMMIT_FILE} --release --bump_type ${VERSION_BUMP_TYPE}	

generate_initial_tagged_commit:
# Create the first version of tagged commit file, used for version update
	git rev-list --max-parents=0 --abbrev-commit HEAD > ${TAGGED_COMMIT_FILE}

format-py:
# Format all the python scripts under this project, excluding submodule and symbolic links
	for f in `find scripts -type f -iname *.py`; \
	do \
	${PYTHON_FORMAT_EXEC} $${f} --line-length 100 || exit 1; \
	done

quick_test:
# Run quick tests (only file generate, no ptpx run)
	${PYTHON_EXEC} test/scripts/run_reg_test.py --config test/common/test_config.yaml --task test/common/quick_test_task_list.yaml --root ${PWD} --j ${NUM_JOBS}

reg_test:
# Run regression tests (full flow run using ptpx)
	${PYTHON_EXEC} test/scripts/run_reg_test.py --config test/common/test_config.yaml --task test/common/reg_test_task_list.yaml --root ${PWD} --j ${NUM_JOBS}

doc:
# Compile documentation in HTML format
	cd docs; echo "Enter docs directory"; \
	make html; \
	cd -

# Functions to extract comments from Makefiles
define COMMENT_EXTRACT
import re
with open ('Makefile', 'r' ) as f:
    matches = re.finditer('^([a-zA-Z-_]*):.*\n#(.*)', f.read(), flags=re.M)
    for _, match in enumerate(matches, start=1):
        header, content = match[1], match[2]
        print(f"  {header:10} {content}")
endef
