#####################################################################
# A script to run tests with a given list of tasks
#####################################################################
import os
from os.path import dirname, abspath
import argparse
import logging
import subprocess
import tarfile
import yaml
import re
import time
from datetime import timedelta
import datetime
import threading
import ezreg_task_manager
import ezreg_job_manager
import ezreg_task_selection

#####################################################################
# Error codes
#####################################################################
error_codes = {"SUCCESS": 0, "ERROR": 1, "FILE_ERROR": 2}

# Constants
__SELECT_ALL_TASKS__ = "all"

#####################################################################
# Initialize logger
#####################################################################
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

##################################################################
# Main function
##################################################################
if __name__ == "__main__":
    # Execute when the module is not initialized from an import statement

    # Parse the options and apply sanity checks
    parser = argparse.ArgumentParser(description="Run regression tests with a given task list ")
    parser.add_argument(
        "--task", required=True, help="A yaml file contains a list of tasks to test"
    )
    parser.add_argument(
        "--task_select",
        default=reg_test_task_selection.ALL_TASK_SELECTED,
        help="Pick the single task to be run. Useful for debugging. The format is [task1,task2,task3]. By default, all tasks are selected",
    )
    parser.add_argument(
        "--new_thread_wait_time",
        type=int,
        default="1",
        help="Specify the waiting time before starting a new thread (unit: second)",
    )
    parser.add_argument(
        "--j", type=int, default=2, help="Specify maximum number of jobs to be run in parallel"
    )
    parser.add_argument(
        "--runtime_dirname", type=str, default="_ezreg_", help="Specify the prefix of the runtime directory to be created"
    )
    parser.add_argument(
        "--dryrun",
        action="store_true",
        help="Perform dry-run without running program. Useful for debugging.",
    )
    parser.add_argument("--output_html_file", help="Output html file for status report")

    args = parser.parse_args()

    num_errors = 0

    # Read task configuration
    task_mgr = ezreg_task_manager.EzRegTaskManager()
    task_mgr.load(args.task)

    # Early exit condition: when no test case is listed
    if task_mgr.empty():
        logging.info("No test case found. Exiting...")
        exit(error_codes["SUCCESS"])

    logging.info(f"Found {task_mgr.num_tasks()} tasks")
    # Preload task selection
    t_sel = ezreg_task_selection.EzRegTaskSelection()
    for t_idx in task_mgr.tasks():
        t_name = task_mgr.task_name(t_idx)
        t_sel.add_predefined_task(t_name)
    t_sel.read_task_selection_str(args.task_select)
    # Report a stats for selected jobs
    logging.info(f"Selected {t_sel.num_selected()}/{t_sel.total()} tasks")
    # Configure job manager
    job_mgr = ezreg_job_manager.EzRegJobManager()
    # Add jobs one by one
    for task_id in task_mgr.tasks():
        job_name = task_mgr.task_name(task_id)
        # Bypass the task which is not selected
        if not t_sel.is_selected(job_name):
            continue
        job_mgr.create_job(job_name, task_mgr.task_command(task_id), task_mgr.task_expect_failure(task_id))
        job_mgr.set_rundir(job_name, task_mgr.task_workspace(task_id))
        # For dependent jobs which are not selected, do not add it to dep list
        # This is to avoid any unexisting blocker to the job run
        actual_job_deps = []
        for task_dep in task_mgr.task_deps(task_id):
            if t_sel.is_selected(task_dep):
                actual_job_deps.append(task_dep)
        job_mgr.set_job_deps(job_name, actual_job_deps)

    # Run jobs
    job_mgr.run_all(args.j, args.dryrun, True)
    num_errors += job_mgr.num_errors()
    if num_errors:
        logging.info(f"Regression jobs finished with {num_errors} errors")
    else:
        logging.info(f"Regression jobs finished successfully")

    if num_errors == 0:
        exit(error_codes["SUCCESS"])
    else:
        exit(error_codes["ERROR"])
