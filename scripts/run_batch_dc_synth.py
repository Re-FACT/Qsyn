#####################################################################
# Python script to execute batch jobs by running Design Compiler Synthesis for a given template tcl script
# This script will
# - Analyze the rtl netlists to get the top-level module with given prefix
# - For each top module
#   - Create the tcl script as synthesis recipe
#   - Run Design Compiler
#   - Analyze output log files and return succeed or failure
#####################################################################

import sys
import os
from os.path import dirname, abspath, isfile
import shutil
import re
import argparse
import logging
import subprocess
import yaml
import run_dc_synth

#####################################################################
# Initialize logger
#####################################################################
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

#####################################################################
# Application (Global variable)
#####################################################################
netlist_name_splitter = ","
error_codes = {"SUCCESS": 0, "ERROR": 1, "OPTION_ERROR": 2, "FILE_ERROR": 3}


#####################################################################
# Main function of this script, so that it can be called by other scripts
#####################################################################
def main(args):
    #####################################################################
    # Parse the options
    #####################################################################
    parser = argparse.ArgumentParser(
        description="Run Synopsys Design Compiler Synthesis for an input netlist"
    )
    parser.add_argument(
        "--rtl_netlists",
        required=True,
        help="Specify the file path to the RTL netlist as input. Use '"
        + netlist_name_splitter
        + "' as a splitter if multiple files are required",
    )
    parser.add_argument(
        "--recipe_template",
        required=True,
        help="Specify the file path to tcl script contain template synthesis recipe",
    )
    parser.add_argument(
        "--technology_library",
        required=True,
        help="Specify the technology library which the RTL netlist will be mapped to",
    )
    parser.add_argument(
        "--project_workspace", required=True, help="Specify the directory to run Design Compiler"
    )
    parser.add_argument(
        "--top_module_prefix",
        default="",
        help="Specify the prefix of top-level module name to be synthesized. All the modules whose name match the prefix will be synthesized",
    )
    parser.add_argument(
        "--config",
        default="",
        help="Specify the yaml file which contains design variables to be replaced in Tcl template files",
    )
    parser.add_argument(
        "--sdc_template", default="", help="Specify the SDC file for design constraints"
    )
    parser.add_argument(
        "--sdc_config", default="", help="Specify the SDC file for design constraints"
    )
    args = parser.parse_args(args)

    # Read a configuration file which contains design variables
    design_var = {}
    sdc_var = {}
    if args.config:
        design_var = run_dc_synth.read_yaml_to_design_variable_database(args.config)
    if args.sdc_config:
        sdc_var = run_dc_synth.read_yaml_to_design_variable_database(args.sdc_config)
    top_modules = get_top_module_names_from_rtl_netlists(args.rtl_netlists, args.top_module_prefix)
    logging.info(f"Found {len(top_modules)} modules to be synthesized:")
    for top_module in top_modules:
        logging.info(f"\t{top_module}")

    logging.info("======== Synthesis jobs starts =========")
    # For each top module, run a synthesis job
    for top_module in top_modules:
        run_dc_synth.run_dc_batch_synth(
            args.rtl_netlists,
            args.recipe_template,
            args.technology_library,
            args.project_workspace,
            top_module,
            design_var,
            sdc_var,
            args.sdc_template,
        )


#####################################################################
# Parse the rtl netlist to get the module name matching the prefix
# Support Verilog only
#####################################################################
def get_top_module_names_from_rtl_netlists(rtl_netlists, top_module_prefix):
    top_modules = []

    # Read each RTL netlist, collect the module name that matches prefix
    for rtl_nlist_file in rtl_netlists.split(netlist_name_splitter):
        with open(rtl_nlist_file, "r") as wp:
            lines = wp.readlines()
            for line_num, curr_line in enumerate(lines):
                if curr_line.startswith("module " + top_module_prefix):
                    for module_name in re.findall("module (\w+)\(", curr_line):
                        top_modules.append(module_name)

    return top_modules


if __name__ == "__main__":
    main(sys.argv[1:])
