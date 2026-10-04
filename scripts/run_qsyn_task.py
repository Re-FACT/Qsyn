#####################################################################
# A script to run a Design Compiler with a given task configuration
#####################################################################
import os
from os.path import dirname, abspath
import glob
import argparse
import logging
import re
import time
from datetime import timedelta
from datetime import datetime
from xml.dom import minidom
import qsyn_tcl_writer
import qsyn_task_manager
import qsyn_device_manager
import qsyn_job_manager
import qsyn_report_manager
import mux_module_manager
import config_mem_manager
from collections import defaultdict, deque

#####################################################################
# Error codes
#####################################################################
error_codes = {"SUCCESS": 0, "ERROR": 1, "FILE_ERROR": 2}

# Constants
QSYN_TCL_FNAME = "run_qsyn.tcl"

space_limit = 80  # Maximum space tuned for the screen width
ALL_TASKS_SELECTED = "all"
first_index = 0

#####################################################################
# Initialize logger
#####################################################################
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


#####################################################################
# Check if the current task name is selected by the given list of task names
#####################################################################
def find_current_task_is_selected(curr_task_name, task_names):
    if task_names == ALL_TASKS_SELECTED:
        return True
    selected_tasks = task_names.split(",")
    if curr_task_name in args.tasks:
        return True
    return False


#####################################################################
# Generate the tcl script for a DC task
def generate_qsyn_tcl_filename(tcldir):
    return os.path.join(os.path.abspath(tcldir), QSYN_TCL_FNAME)


#####################################################################
# Generate the common parts of tcl script for a DC task which can fit multiple purpose:
# - load design
# - load pdk
#####################################################################
def generate_qsyn_tcl_common_part(tcl_writer, task_mgr, device_mgr, use_custom_pdk):
    num_errors = 0

    # Add db one by one
    pvt_corner_label = task_mgr.technology_corner()
    db_root = task_mgr.technology_root()
    if use_custom_pdk:
        db_root = ""
    for sc_lib in device_mgr.standard_cell_libs(db_root, pvt_corner_label):
        tcl_writer.add_db(sc_lib)

    for link_lib in task_mgr.netlist_link_path():
        tcl_writer.add_db(os.path.abspath(link_lib))

    num_nlists = 0

    # Add netlist one by one
    nlist_root_dir = task_mgr.netlist_input()
    logging.info(f"Including netlist files under '{nlist_root_dir}'")
    for src_file_postfix in tcl_writer.netlist_file_filter():
        for root, dirs, files in os.walk(nlist_root_dir, followlinks=True):
            for src_file in files:
                # Skip the files which should be excluded
                if src_file in task_mgr.netlist_exclude_files():
                    continue
                src_file_path = os.path.join(root, src_file)
                # Only focus on specific file types
                if not src_file.endswith(src_file_postfix):
                    continue
                src_file_path = os.path.join(root, src_file)
                # Identify system verilog netlists
                nlist_ftype = tcl_writer.auto_find_netlist_file_type(src_file)
                for curr_filter in task_mgr.netlist_system_verilog_filter():
                    if re.match(re.compile(re.escape(curr_filter)), src_file):
                        logging.info(
                            f"Force netlist '{src_file}' to be treated as System Verilog as defined in task configuration"
                        )
                        nlist_ftype = qsyn_tcl_writer.SYSTEM_VERILOG_FILE_TYPE
                tcl_writer.add_netlist(os.path.abspath(src_file_path), nlist_ftype)
                num_nlists += 1
    logging.info(f"Found and included {num_nlists} netlist files'")

    return num_errors


#####################################################################
# Adjust the subblocks execution order based on dependencies
#####################################################################
def process_subblocks_depends(task_id):

    # 1. Build dependency graph: {task name: list of dependent task names}
    dependencies = {}
    subblocks = task_mgr.synth_task_subblocks(task_id)

    for subblocks_id in range(len(subblocks)):
        subblock_name = task_mgr.synth_task_subblocks_name(task_id, subblocks_id)
        dependencies[subblock_name] = task_mgr.synth_task_subblocks_depends(task_id, subblocks_id)
    # 2. order subblocks
    all_tasks = set(dependencies.keys())
    name_to_idx = {name: idx for idx, name in enumerate(dependencies.keys())}
    in_degree = {task: len(deps) for task, deps in dependencies.items()}
    adjacency = defaultdict(list)
    for task, deps in dependencies.items():
        for dep in deps:
            adjacency[dep].append(task)
    # 3. Initialize the queue: tasks with an in-degree of 0 (no dependencies)s
    queue = deque([task for task in all_tasks if in_degree[task] == 0])
    execution_order = []
    # 4. Execute the topological sort
    while queue:
        current = queue.popleft()
        execution_order.append(current)
        for next_task in adjacency[current]:
            in_degree[next_task] -= 1
            if in_degree[next_task] == 0:
                queue.append(next_task)
    # 5. Check for cyclic dependencies (if the length of the execution order is insufficient, it indicates a cycle)
    if len(execution_order) != len(all_tasks):
        unexecuted = [task for task in all_tasks if task not in execution_order]
        raise ValueError(
            f"Cyclic dependencies exist, and the tasks involved in the cycle{unexecuted}"
        )
    return execution_order, name_to_idx


#####################################################################
# Generate the tcl script for a DC task for report timing purpose
#####################################################################
def generate_qsyn_tcl_file(
    tclfname,
    use_custom_pdk,
    task_mgr,
    device_mgr,
    task_id,
    design_id,
    mux_module_mgr,
    config_mem_mgr,
):
    # Log runtime
    start_time = time.time()

    num_errors = 0

    logging.info("Writing tcl file '" + str(tcl_fname) + "'...")

    tcl_writer = qsyn_tcl_writer.QsynTclWriter()

    num_errors += generate_qsyn_tcl_common_part(tcl_writer, task_mgr, device_mgr, use_custom_pdk)

    # Organize the variable for target library
    target_sc_libs = []
    db_root = task_mgr.technology_root()
    pvt_corner_label = task_mgr.technology_corner()
    if use_custom_pdk:
        db_root = ""

    if task_mgr.synth_task_require_compile(task_id):
        for sc_lib_tag in task_mgr.synth_task_target_library(task_id):
            curr_target_sc_lib = device_mgr.find_standard_cell_library_by_tag(
                db_root, pvt_corner_label, sc_lib_tag
            )
            if not curr_target_sc_lib:
                raise Exception(f"Invalid standard cell library name '{sc_lib_tag}'")
            target_sc_libs.append(curr_target_sc_lib)
        tcl_writer.add_appvar("target_library", '"' + " ".join(target_sc_libs) + '"')

    # Add variables for micro floorplan synth
    design_name = task_mgr.synth_task_current_design(task_id, design_id)
    if config_mem_mgr.is_valid():
        tcl_writer.set_config_group_mem(config_mem_mgr.config_group_mem(design_name))
    if mux_module_mgr.is_valid():
        for mux_name in mux_module_mgr.mux_names(design_name):
            tcl_writer.add_mux_name(mux_name)
    top_flatten = task_mgr.synth_task_top_flattern(task_id)
    if top_flatten:
        tcl_writer.set_synth_task_top_flatten(True)
    ## Add subblocks compile
    execution_order, name_to_idx = process_subblocks_depends(task_id)
    for subblock_task in execution_order:
        pattern = task_mgr.synth_task_subblocks_pattern(task_id, name_to_idx[subblock_task])
        flatten = task_mgr.synth_task_subblocks_flattern(task_id, name_to_idx[subblock_task])
        tcl_writer.add_subblocks(subblock_task)
        tcl_writer.add_subblocks_pattern_map(subblock_task, [pattern, flatten])
        tcl_writer.set_subblocks_current_design(True)
        tcl_writer.set_subblocks_target_design(True)
        if task_mgr.synth_task_subblocks_target_library_option(
            task_id, name_to_idx[subblock_task]
        ) and task_mgr.synth_task_subblocks_target_library_subset(
            task_id, name_to_idx[subblock_task]
        ):
            tcl_writer.set_subblocks_target_library_subset(True)
            subset_path = task_mgr.synth_task_subblocks_target_library_subset(
                task_id, name_to_idx[subblock_task]
            )
            subset = " ".join(subset_path)
            tcl_writer.get_subblocks_target_library_subset(subset)
        sdc_file = task_mgr.synth_task_subblocks_sdc(task_id, name_to_idx[subblock_task])[
            first_index
        ]
        if sdc_file:
            tcl_writer.set_subblocks_sdc(True)
            tcl_writer.get_source_subblock_tcl_file(subblock_task, os.path.abspath(sdc_file))
        # Add subblock sdc
        # print("sdc_file*****************",task_mgr.synth_task_subblocks_sdc(task_id, name_to_idx[subblock_task]))
        # for sdc_f in task_mgr.synth_task_subblocks_sdc(task_id,name_to_idx[subblock_task]):
        #     tcl_writer.add_subblock_sdc(sdc_f)
        compile = task_mgr.synth_task_subblocks_compile(task_id, name_to_idx[subblock_task])
        tcl_writer.set_subblocks_compile(subblock_task, compile)
        if task_mgr.synth_task_subblocks_compile(task_id, name_to_idx[subblock_task]):
            tcl_writer.set_subblock_compile_type(
                task_mgr.synth_task_subblocks_compile_type(task_id, name_to_idx[subblock_task])
            )
            tcl_writer.set_subblock_compile_optimization(
                task_mgr.synth_task_subblocks_compile_optimize(task_id, name_to_idx[subblock_task])
            )
            tcl_writer.set_subblock_compile_effort(
                task_mgr.synth_task_subblocks_compile_effort(task_id, name_to_idx[subblock_task])
            )
        if task_mgr.synth_task_subblocks_rename_prefix(task_id, name_to_idx[subblock_task]):
            tcl_writer.set_subblock_rename_prefix(True)

    # Add sdc
    for sdc_f in task_mgr.synth_task_sdc(task_id):
        tcl_writer.add_sdc(os.path.abspath(sdc_f))
    for sdc_f in task_mgr.synth_task_post_compile_sdc(task_id):
        tcl_writer.add_post_compile_sdc(sdc_f)

    # Specify the design name only for report timing
    tcl_writer.set_design_name(task_mgr.synth_task_current_design(task_id, design_id))
    tcl_writer.set_remove_time_stamp(task_mgr.synth_task_remove_time_stamp(task_id))
    tcl_writer.set_use_name_rule(task_mgr.synth_task_use_name_rule(task_id))
    tcl_writer.set_check_timing(task_mgr.synth_task_get_check_timing_rpt(task_id, design_id))

    # Specify compilation style
    if task_mgr.synth_task_require_compile(task_id):
        tcl_writer.set_compile_type(task_mgr.synth_task_compile_type(task_id))
        tcl_writer.set_compile_optimization(task_mgr.synth_task_compile_optimization(task_id))
        tcl_writer.set_compile_effort(task_mgr.synth_task_compile_effort(task_id))

        # Specify the synthesized netlist file
        synth_nlist = os.path.join(
            os.path.abspath(task_mgr.netlist_output()),
            task_mgr.synth_task_current_design(task_id, design_id),
        )
        tcl_writer.set_write_design_file(synth_nlist)

    # Enable report P.P.A.
    if task_mgr.synth_task_report_area(task_id):
        tcl_writer.set_report_area(True)
        tcl_writer.set_report_area_file(task_mgr.synth_task_report_area_file(task_id, design_id))

    if task_mgr.synth_task_report_timing(task_id):
        tcl_writer.set_report_timing(True)
        tcl_writer.set_report_timing_file(
            task_mgr.synth_task_report_timing_file(task_id, design_id)
        )

    if task_mgr.synth_task_report_power(task_id):
        tcl_writer.set_report_power(True)
        tcl_writer.set_report_power_file(task_mgr.synth_task_report_power_file(task_id, design_id))
        tcl_writer.set_report_power_hierarchy(task_mgr.synth_task_report_power_hierarchy(task_id))

    if task_mgr.synth_task_check_timing(task_id):
        tcl_writer.set_check_timing_rpt(True)
        tcl_writer.set_check_timing_rpt_file(
            task_mgr.synth_task_get_check_timing_rpt(task_id, design_id)
        )

    # Decide if we should save the session after synthesis task is accomplished
    if task_mgr.synth_task_save_session(task_id):
        tcl_writer.set_session_name(task_mgr.synth_task_session_name(task_id, design_id))

    # Output to file
    os.makedirs(os.path.dirname(tcl_fname), exist_ok=True)
    tcl_writer.write(tcl_fname)

    end_time = time.time()
    time_diff = timedelta(seconds=(end_time - start_time))

    time_str = "Write tcl took " + str(time_diff)
    logging.info(time_str)

    return num_errors


#####################################################################
# Main function
#####################################################################
if __name__ == "__main__":
    # Execute when the module is not initialized from an import statement

    # Parse the options and apply sanity checks
    parser = argparse.ArgumentParser(description="Run a synthesis task for netlist synthesis")
    parser.add_argument("--config", required=True, help="The task configuration file")
    parser.add_argument(
        "--mux_modules",
        default=None,
        help="The YAML file contains definition for unique MUX modules under each programmable blocks",
    )
    parser.add_argument(
        "--config_mem_instances",
        default=None,
        help="The YAML file contains definition for unique configuration memory instances under each programmable blocks",
    )
    parser.add_argument(
        "--report_summary",
        default="report_summary.csv",
        help="The summary report extracted from the original synthesis report generated by synthesis tools",
    )
    parser.add_argument(
        "--root_directory",
        default=".",
        help="The root directory to search pdk, netlists etc. which are required by the task",
    )
    parser.add_argument(
        "--pdk_config",
        required=True,
        help="The PDK configuration for a PDK. Once defined, the pdk setting in your task configuration will be overwritten except the corner selection.",
    )
    parser.add_argument(
        "--file_generation_only",
        action="store_true",
        help="Only generate input files for synthesis flow, skip running synthesis",
    )
    parser.add_argument(
        "--parse_report_only",
        action="store_true",
        help="Only parse the reports and generate a report summary, skip file generation and running DC",
    )
    parser.add_argument(
        "--tasks",
        default=ALL_TASKS_SELECTED,
        help="Specify the names of synthesis tasks to be executed. This allows users to select one or a number of tasks to be run. Use comma as a splitter, e.g., task1,task2,task3. By default, run all the listed tasks.",
    )
    parser.add_argument(
        "--qsyn_rundir",
        default="_snps_qsyn",
        help="The runtime directory to execute synthesis task",
    )

    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default="2",
        help="The maximum number of jobs to be run in parallel",
    )

    # Log runtime
    start_time = time.time()

    args = parser.parse_args()

    num_errors = 0

    # Read task configuration
    task_mgr = qsyn_task_manager.QsynTaskManager()
    task_mgr.load(args.config)

    # Read device data based on the selection in task configuration
    device_mgr = qsyn_device_manager.QsynDeviceManager()
    use_custom_pdk = False
    if args.custom_pdk:
        use_custom_pdk = True
        logging.info("Use the custom PDK settings provided by users")
        device_mgr.load(args.custom_pdk)
    else:
        logging.info("Use the built-in PDK settings")
        device_data_file = task_mgr.technology_data_file(args.root_directory)
        device_mgr.load(device_data_file)

    # Load mux modules if provided
    mux_module_mgr = mux_module_manager.MuxModuleManager()
    if args.mux_modules:
        mux_module_mgr.load(args.mux_modules)
    # Load mux modules if provided
    config_mem_mgr = config_mem_manager.ConfigMemManager()
    if args.config_mem_instances:
        config_mem_mgr.load(args.config_mem_instances)

    job_mgr = qsyn_job_manager.QsynJobManager()
    job_mgr.set_runtime_dir_prefix(args.qsyn_rundir)
    rpt_mgr = qsyn_report_manager.QsynReportManager()
    rpt_dir = []
    # For each task: area analysis, power analysis or timing analysis task
    # Create a separated runtime directory and run
    logging.info("Num. synth. tasks is " + str(len(task_mgr.synth_tasks())))
    for synth_task_id in task_mgr.synth_tasks():
        # Filter out the unselected tasks
        curr_task_selected = find_current_task_is_selected(
            task_mgr.synth_task_name(synth_task_id), args.tasks
        )
        mode = task_mgr.synth_task_mode(synth_task_id)
        if not curr_task_selected:
            continue
        for curr_design_id in task_mgr.synth_task_current_designs(synth_task_id):
            job_name = (
                task_mgr.synth_task_name(synth_task_id)
                + "_"
                + task_mgr.synth_task_current_design(synth_task_id, curr_design_id)
            )
            job_mgr.create_job(job_name, mode)
            dc_job_rundir = job_mgr.dc_rundir(job_name)
            # Generate tcl script to run PTPX
            tcl_fname = generate_dc_tcl_filename(dc_job_rundir)
            if not args.parse_report_only:
                num_errors += generate_dc_tcl_file(
                    tcl_fname,
                    use_custom_pdk,
                    task_mgr,
                    device_mgr,
                    synth_task_id,
                    curr_design_id,
                    mux_module_mgr,
                    config_mem_mgr,
                )
            job_mgr.set_tcl_script(job_name, tcl_fname)
            if task_mgr.synth_task_report_area(synth_task_id):
                curr_area_rpt_file = task_mgr.synth_task_report_area_file(
                    synth_task_id, curr_design_id
                )
                rpt_dir.append(curr_area_rpt_file)
                rpt_mgr.add_area_report_file(
                    curr_area_rpt_file,
                    task_mgr.synth_task_current_design(synth_task_id, curr_design_id),
                )
            if task_mgr.synth_task_report_timing(synth_task_id):
                rpt_dir.append(
                    task_mgr.synth_task_report_timing_file(synth_task_id, curr_design_id)
                )
            if task_mgr.synth_task_report_power(synth_task_id):
                rpt_dir.append(task_mgr.synth_task_report_power_file(synth_task_id, curr_design_id))

    # Run DC and check errors
    if args.file_generation_only or args.parse_report_only:
        logging.info("User selects to skip running DC.")
    else:
        # Create report directories so that primetime do not stop on the error
        for rdir in rpt_dir:
            os.makedirs(os.path.dirname(rdir), exist_ok=True)
        job_mgr.run_dc_all(args.jobs, True)
        num_errors += job_mgr.num_errors()
        if num_errors:
            logging.info(f"DC job finished with {num_errors} errors")
        else:
            logging.info(f"DC job finished successfully")

    if args.parse_report_only:
        # Read DC reports and generate final report
        logging.info(f"Generating DC report summary...")
        rpt_mgr.write_report_summary(args.report_summary)
        logging.info(f"Done")

    end_time = time.time()
    time_diff = timedelta(seconds=(end_time - start_time))

    time_str = "Running Design Compiler flow took " + str(time_diff)
    logging.info(time_str)

    if num_errors == 0:
        exit(error_codes["SUCCESS"])
    else:
        exit(error_codes["ERROR"])
