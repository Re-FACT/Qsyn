#####################################################################
# Python script to execute Design Compiler Synthesis for a given template tcl script
# This script will
# - Create the tcl script as synthesis recipe
# - Run Design Compiler
# - Analyze output log files and return succeed or failure
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
        "--top_module",
        default="",
        help="Specify top-level module name to be synthesized. This is required when there are more than 1 RTL netlist or module. When specified, only the specified module will be synthesized. Otherwise, each module found in the RTL netlists will be synthesized",
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
        design_var = read_yaml_to_design_variable_database(args.config)
    if args.sdc_config:
        sdc_var = read_yaml_to_design_variable_database(args.sdc_config)
    run_dc_batch_synth(
        args.rtl_netlists,
        args.recipe_template,
        args.technology_library,
        args.project_workspace,
        args.top_module,
        design_var,
        sdc_var,
        args.sdc_template,
    )


#####################################################################
# Read task list from a yaml file
#####################################################################
def read_yaml_to_design_variable_database(yaml_filename):
    design_var_db = {}
    with open(yaml_filename, "r") as stream:
        try:
            design_var_db = yaml.load(stream, Loader=yaml.FullLoader)
            logging.info(
                "Found "
                + str(len(design_var_db))
                + " design variables to replace in template script"
            )
        except yaml.YAMLError as exc:
            logging.error(exc)
            exit(error_codes["FILE_ERROR"])

    return design_var_db


#####################################################################
# A function to execute a single-run of Design Compiler for a RTL design
#####################################################################
def run_dc_synth(
    rtl_netlists,
    rtl_design_name,
    recipe_template,
    technology_library,
    project_workspace,
    design_var,
    sdc_var,
    sdc_template,
):
    project_abs_path = os.path.abspath(project_workspace)
    if not os.path.isdir(project_abs_path):
        logging.debug("Creating Design Compiler project directory : " + project_abs_path + " ...\n")
        os.makedirs(project_abs_path, exist_ok=True)
        logging.debug("Done\n")

    # Generate the string for the RTL netlists, which will be used in the auto-generated Tcl script
    rtl_netlist_str = "{" + " ".join(rtl_netlists) + "}"

    #####################################################################
    # Create the Tcl script for Custom SDC Values
    #####################################################################
    # Get absolute path to the template tcl script, it must be valid
    template_tcl_path = os.path.abspath(sdc_template)
    if isfile(template_tcl_path):

        # Create output file handler
        tcl_file_path = project_abs_path + "/" + os.path.basename(rtl_design_name) + "_dc.sdc"
        logging.info("Generating Tcl script from template recipe: " + tcl_file_path)

        tcl_file = open(tcl_file_path, "w")

        with open(template_tcl_path, "r") as wp:
            template_tcl_file = wp.readlines()
            for line_num, curr_line in enumerate(template_tcl_file):
                line2output = curr_line
                for key in sdc_var:
                    # line2output = re.sub(str(key).upper() + ".*", str(key).upper + " " + str(sdc_var[key]), line2output)
                    line2output = re.sub(
                        "set " + str(key).upper() + ".*",
                        "set " + str(key).upper() + " " + str(sdc_var[key]),
                        line2output,
                    )
                # Finished processing
                # Output the line
                tcl_file.write(line2output)

        tcl_file.close()
        line2output = {}
    #####################################################################
    # Create the Tcl script for Design Compiler
    #####################################################################
    # Get absolute path to the template tcl script, it must be valid
    template_tcl_path = os.path.abspath(recipe_template)
    assert isfile(template_tcl_path)

    # Create output file handler
    tcl_file_path = project_abs_path + "/" + os.path.basename(rtl_design_name) + "_dc.tcl"
    logging.debug("Generating Tcl script from template recipe: " + tcl_file_path)

    tcl_file = open(tcl_file_path, "w")

    with open(template_tcl_path, "r") as wp:
        template_tcl_file = wp.readlines()
        for line_num, curr_line in enumerate(template_tcl_file):
            line2output = curr_line
            # Replace keywords with custom values
            line2output = re.sub("TECH_DB_VAR", technology_library, line2output)
            line2output = re.sub("DESIGN_NAME_VAR", rtl_design_name, line2output)
            line2output = re.sub("RTL_NETLIST_VAR", rtl_netlist_str, line2output)
            # Replace keywords from design variable database
            for key in design_var:
                line2output = re.sub(str(key).upper() + "_VAR", str(design_var[key]), line2output)
            # Finished processing
            # Output the line
            tcl_file.write(line2output)

    tcl_file.close()
    logging.debug("Done")

    #####################################################################
    # Run Design Compiler
    #####################################################################
    curr_dir = os.getcwd()
    # Change to the project directory
    os.chdir(project_abs_path)
    logging.debug("Changed to directory: " + project_abs_path)

    # Run Design Compiler
    dc_log_file_path = project_abs_path + "/" + os.path.basename(rtl_design_name) + "_dc.log"
    dc_shell_bin = "dc_shell"
    dc_shell_cmd = dc_shell_bin + " -f " + os.path.abspath(tcl_file_path) + " > " + dc_log_file_path
    logging.debug("Running Design Compiler by : " + dc_shell_cmd)
    subprocess.run(dc_shell_cmd, shell=True, check=True)

    # Go back to current directory
    os.chdir(curr_dir)


#####################################################################
# Main function of this script, so that it can be called by other scripts
#####################################################################
def run_dc_batch_synth(
    rtl_netlists,
    recipe_template,
    technology_library,
    project_workspace,
    top_module,
    design_var,
    sdc_var,
    sdc_template,
):
    #####################################################################
    # Check options:
    # - Input files must be valid
    #   Otherwise, error out
    #####################################################################
    for rtl_netlist in rtl_netlists.split(netlist_name_splitter):
        if not isfile(rtl_netlist):
            logging.error("Invalid RTL netlist: " + rtl_netlist + "\nFile does not exist!\n")
            exit(error_codes["FILE_ERROR"])

    if not isfile(recipe_template):
        logging.error("Invalid recipe template: " + recipe_template + "\nFile does not exist!\n")
        exit(error_codes["FILE_ERROR"])

    if not isfile(technology_library):
        logging.error(
            "Invalid technology library: " + technology_library + "\nFile does not exist!\n"
        )
        exit(error_codes["FILE_ERROR"])

    #####################################################################
    # Collect all the RTL designs to synthesis from the RTL netlist
    #####################################################################
    rtl_design_names = []
    for rtl_netlist in rtl_netlists.split(","):
        with open(rtl_netlist, "r") as wp:
            rtl_file = wp.readlines()
            # If a line starts with 'module', it is an RTL design to be synthesized
            for line_num, curr_line in enumerate(rtl_file):
                if curr_line.startswith("module"):
                    # Get the design name
                    rtl_design_name = re.findall("module(\s+)(\w+)(\s*)\(", curr_line)[0][1]
                    rtl_design_names.append(rtl_design_name)

    if len(top_module) == 0:
        logging.info("Found " + str(len(rtl_design_names)) + " RTL designs to synthesize")

    # Get absolute path to the rtl netlists, it must be valid
    rtl_netlists_abspath = []
    for rtl_netlist in rtl_netlists.split(","):
        cur_abspath = os.path.abspath(rtl_netlist)
        rtl_netlists_abspath.append(cur_abspath)
        assert isfile(cur_abspath)

    if len(top_module) == 0:
        curr_case = 0
        for rtl_design_name in rtl_design_names:
            logging.info(
                "["
                + str(curr_case)
                + "/"
                + str(len(rtl_design_names))
                + "] "
                + "Running Design Compiler for design: "
                + rtl_design_name
            )
            run_dc_synth(
                rtl_netlists_abspath,
                rtl_design_name,
                recipe_template,
                technology_library,
                project_workspace,
                design_var,
                sdc_var,
                sdc_template,
            )
            logging.info("Done")
            curr_case += 1
    else:
        # User specificies a top_module. Must validate that the top module is in the design name list
        if top_module in rtl_design_names:
            logging.info("Running Design Compiler for design: " + top_module)
            run_dc_synth(
                rtl_netlists_abspath,
                top_module,
                recipe_template,
                technology_library,
                project_workspace,
                design_var,
                sdc_var,
                sdc_template,
            )
            logging.info("Done")
        else:
            # Error out if top-module is not specified
            logging.error("Top module '" + top_module + "' is not found in the RTL netlists!")
            logging.error("Candidate top modules are '" + rtl_design_names + "'")
            exit(error_codes["ERROR"])


if __name__ == "__main__":
    main(sys.argv[1:])
