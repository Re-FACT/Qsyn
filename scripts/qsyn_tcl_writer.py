import os
import logging

# Constants
CMD_SEARCH_PATH = "search_path"
CMD_LINK_PATH = "link_path"
CMD_TARGET_LIBRARY = "target_library"
SYSTEM_VERILOG_FILE_TYPE = "system_verilog_file_type"
VERILOG_FILE_TYPE = "verilog_file_type"
SUBBLOCK_NAME = "TOP_DESIGN_NAME"
SUBBLOCK_CURRENT_DESIGN = "current_design"
SUBBLOCK_TARGET_DESIGN = "TARGET_DESIGN"
SUBBLOCK_GET_DESIGN = "get designs"
pattern_idx = 0
flatten_idx = 1
GET_LIB_CELLS = "get_lib_cells"

# Support tools
TOOL_SNPS_DC = "snps_dc"
TOOL_YOSYS = "yosys"
SUPPORTED_TOOLS = [
  TOOL_YOSYS,
  TOOL_SNPS_DC
]

# Class of A general purpose Design Compiler Tcl writer
class QsynTclWriter:
    def __init__(self):
        # constants
        self.__VERILOG_NETLIST_FILES_VAR_NAME_ = "VERILOG_NETLIST_FILES"
        self.__SVERILOG_NETLIST_FILES_VAR_NAME_ = "SVERILOG_NETLIST_FILES"
        self.__tool_ = ""
        # Internal data
        self.__design_name_ = ""
        self.__appvars_ = {}
        self.__localvars_ = {
            self.__VERILOG_NETLIST_FILES_VAR_NAME_: "[list ]",
            self.__SVERILOG_NETLIST_FILES_VAR_NAME_: "[list ]",
        }
        self.__dbs_ = []
        self.__target_libs_ = []
        self.__netlists_ = []
        self.__netlist_types_ = []
        self.__sdcs_ = []
        self.__subblock_sdc_ = []
        self.__post_compile_sdcs_ = []
        self.__opt_recipe_ = {}
        self.__subblock_opt_recipe_ = {}
        self.__session_name_ = ""
        self.__report_area_ = False
        self.__report_area_options_ = {}
        self.__report_timing_ = False
        self.__report_timing_options_ = {}
        self.__report_power_ = False
        self.__report_power_options_ = {}
        self.__write_design_file_ = ""
        self.__remove_time_stamp_ = True
        self.__use_name_rule_ = True
        self.__config_group_mem_ = ""
        self.__mux_name_list_ = []
        self.__subblocks_current_design_ = False
        self.__subblocks_target_design_ = False
        self.__subblocks_get_design_ = ""
        self.__subblocks_name_ = []
        self.__subblocks_pattern_ = ""
        self.__subblocks_pattern_map_ = {}
        self.__subblocks_flatten_ = False
        self.__synth_task_top_flatten_ = False
        self.__subblocks_compile_ = {}
        self.__subblocks_library_subset_ = False
        self.__target_library_var_ = ""
        self.__subblocks_sdc_ = False
        self.__subblocks_sdc_file_name = ""
        self.__subblocks_rename_prefix = False
        self.__subblocks_sdc_file_name_map = {}
        self.__check_timing_rpt_ = False
        self.__check_timing_rpt_file_ = ""
        # Internal counter
        self.__v_nlist_cnt_ = 0  # Verilog netlist number
        self.__sv_nlist_cnt_ = 0  # System Verilog netlist number

    def __check_valid_tool(self):
        if self.__tool_ not in SUPPORTED_TOOLS:
            raise Exception(f"Synthesis tool '{self.__tool_}' is not in the list of supported tools.\nExpect: {SUPPORTED_TOOLS}\n")

    # Set the synthesis tool
    def set_tool(self, val):
        self.__tool_ = val

    # Support netlist file types
    # - Verilog and its compressed copy
    # - System Verilog and its compressed copy
    def netlist_file_filter(self):
        return [".v", ".v.gz", ".sv", ".sv.gz"]

    # Automatically find the netlist file type
    def auto_find_netlist_file_type(self, fname):
        if fname.endswith(".v") or fname.endswith(".v.gz"):
            return VERILOG_FILE_TYPE
        if fname.endswith(".sv") or fname.endswith(".sv.gz"):
            logging.info(f"Automatically infer netlist '{fname}' to be System Verilog")
            return SYSTEM_VERILOG_FILE_TYPE
        # Unable to identify the file type, return an empty string
        return ""

    def set_design_name(self, val):
        self.__design_name_ = val

    def add_appvar(self, var, val):
        self.__appvars_[var] = val

    def add_localvar(self, var, val):
        self.__localvars_[var] = val

    def add_db(self, val):
        self.__dbs_.append(val)

    def set_target_lib(self, val):
        self.__target_libs_ = val

    def add_subblocks(self, val):
        self.__subblocks_name_.append(val)

    def add_subblocks_pattern_map(self, key, val):
        self.__subblocks_pattern_map_[key] = val

    def add_netlist(self, val, ftype):
        self.__netlists_.append(val)
        if ftype:
            # Ensure it is a proper type
            if ftype not in [VERILOG_FILE_TYPE, SYSTEM_VERILOG_FILE_TYPE]:
                raise Exception(
                    "Invalid file type for netlist! Currently support Verilog and SystemVerilog\n"
                )
            self.__netlist_types_.append(ftype)
        else:
            # By default, treat as verilog
            self.__netlist_types_.append(VERILOG_FILE_TYPE)

    def add_sdc(self, val):
        self.__sdcs_.append(val)

    def add_subblock_sdc(self, val):
        self.__subblock_sdc_.append(val)

    def add_post_compile_sdc(self, val):
        self.__post_compile_sdcs_.append(val)

    def set_report_area(self, val):
        self.__report_area_ = val

    def set_report_area_file(self, val):
        self.__report_area_options_["file"] = val

    def set_report_power(self, val):
        self.__report_power_ = val

    def set_report_power_file(self, val):
        self.__report_power_options_["file"] = val

    def set_report_power_hierarchy(self, val):
        self.__report_power_options_["hierarchy"] = val

    def set_report_timing(self, val):
        self.__report_timing_ = val

    def set_report_timing_file(self, val):
        self.__report_timing_options_["file"] = val

    def set_check_timing_rpt(self, val):
        self.__check_timing_rpt_ = val

    def set_check_timing_rpt_file(self, val):
        self.__check_timing_rpt_file_ = val

    def set_write_design_file(self, val):
        self.__write_design_file_ = val

    def set_subblocks_current_design(self, val):
        self.__subblocks_current_design_ = val

    def set_subblocks_target_design(self, val):
        self.__subblocks_target_design_ = val

    def set_subblocks_get_design(self, val):
        cmd = SUBBLOCK_GET_DESIGN + " " + val
        self.__subblocks_get_design_ = cmd

    def set_subblocks_flatten(self, val):
        self.__subblocks_flatten_ = val

    def set_synth_task_top_flatten(self, val):
        self.__synth_task_top_flatten_ = val

    def set_subblocks_compile(self, key, val):
        self.__subblocks_compile_[key] = val

    def set_subblocks_target_library_subset(self, val):
        self.__subblocks_library_subset_ = val

    def set_optimization_recipe(self, val):
        self.__opt_recipe_ = val

    def set_subblock_optimization_recipe(self, val):
        self.__subblock_opt_recipe_ = val

    def get_subblocks_target_library_subset(self, val):
        self.__target_library_var_ = val

    def set_subblocks_sdc(self, val):
        self.__subblocks_sdc_ = val

    def set_remove_time_stamp(self, val):
        self.__remove_time_stamp_ = val

    def set_use_name_rule(self, val):
        self.__use_name_rule_ = val

    def set_check_timing(self, val):
        self.__check_timing_rpt_ = val

    def get_source_subblock_tcl_file(self, key, val):
        self.__subblocks_sdc_file_name = val
        self.__subblocks_sdc_file_name_map[key] = val

    def set_subblock_rename_prefix(self, val):
        self.__subblocks_rename_prefix = val

    # Create a line of comments
    def __write_comment_line(self, fp, line_str):
        fp.write("# " + line_str + "\n")

    # Create a line of appvar
    def __write_setvar_line(self, fp, var, val):
        fp.write("set " + var + " " + val + "\n")

    # Create a line of appvar with []
    def __write_setvar_line_priority(self, fp, var, val):
        fp.write(f"set {var} [{val}]\n")

    # create a line for target design with []
    def __write_setvar_line_priority_target_design(self, fp, var, val):
        fp.write(f"set {var} [get_object_name [{val}]]\n")

    # Create a line of set target library subset
    def __write_setvar_target_library_subset(self, fp, var, val):
        fp.write(f"set_target_library_subset {var} [{val}]\n")

    # Create a line of set subblock target designs
    def __write_subblock_current_design_target_design(self, fp):
        fp.write(f"{SUBBLOCK_CURRENT_DESIGN} ${{TARGET_DESIGN}}\n")

    # Create a line of set subblock current designs
    def __write_subblock_current_design_top_design_name(self, fp):
        fp.write(f"{SUBBLOCK_CURRENT_DESIGN} ${{TOP_DESIGN_NAME}}\n")

    # Create a line of appvar
    def __write_read_db_line(self, fp, val):
        self.__check_valid_tool()
        if self.__tool_ == TOOL_SNPS_DC:
            fp.write("read_db " + val + "\n")
        if self.__tool_ == TOOL_YOSYS:
            fp.write("read_liberty -lib " + val + "\n")

    # Create a line of appvar
    def __yosys_write_add_verilog_line(self, fp, val, ftype):
        if ftype == SYSTEM_VERILOG_FILE_TYPE:
            fp.write("read_verilog -sv " + self.__SVERILOG_NETLIST_FILES_VAR_NAME_ + " " + val + "\n")
            self.__sv_nlist_cnt_ += 1
        elif ftype == VERILOG_FILE_TYPE:
            fp.write("read_verilog " + self.__VERILOG_NETLIST_FILES_VAR_NAME_ + " " + val + "\n")
            self.__v_nlist_cnt_ += 1
        else:
            raise Exception(
                "Invalid file type for netlist! Currently support Verilog and SystemVerilog\n"
            )

    # Create a line of appvar
    def __snps_dc_write_add_verilog_line(self, fp, val, ftype):
        if ftype == SYSTEM_VERILOG_FILE_TYPE:
            fp.write("lappend " + self.__SVERILOG_NETLIST_FILES_VAR_NAME_ + " " + val + "\n")
            self.__sv_nlist_cnt_ += 1
        elif ftype == VERILOG_FILE_TYPE:
            fp.write("lappend " + self.__VERILOG_NETLIST_FILES_VAR_NAME_ + " " + val + "\n")
            self.__v_nlist_cnt_ += 1
        else:
            raise Exception(
                "Invalid file type for netlist! Currently support Verilog and SystemVerilog\n"
            )

    # Create a line of appvar
    def __write_analyze_design_line(self, fp):
        if self.__v_nlist_cnt_ > 0:
            fp.write("analyze -f verilog ${" + self.__VERILOG_NETLIST_FILES_VAR_NAME_ + "}\n")
        if self.__sv_nlist_cnt_ > 0:
            fp.write("analyze -f sverilog ${" + self.__SVERILOG_NETLIST_FILES_VAR_NAME_ + "}\n")

    def __write_elaborate_design_line(self, fp, val):
        self.__check_valid_tool()
        if self.__tool_ == TOOL_SNPS_DC:
            fp.write(f"elaborate {val}\n")
        if self.__tool_ == TOOL_YOSYS:
            fp.write(f"hierarchy -check -top {val}\n")
            if self.__synth_task_top_flatten_:
                fp.write(f"flatten\n")

    # Create a line of appvar
    def __write_read_sdc_line(self, fp, val):
        fp.write("read_sdc " + val + "\n")

    # Create a line of appvar
    def __write_source_tcl_line(self, fp, val):
        fp.write("source " + val + "\n")

    # Create a line of appvar
    def __write_read_activity_line(self, fp, val, strip_path):
        fp.write("read_saif " + val + " -strip_path " + strip_path + "\n")

    # Create a line of flatten
    def __write_flatten_line(self, fp):
        fp.write("ungroup -flatten -all\n")

    # Create a line of report_area
    def __write_report_area_line(self, fp, rptf, remove_time_stamp):
        fp.write("file mkdir " + os.path.dirname(rptf) + "\n")
        fp.write('redirect -file "' + rptf + '" {\n')
        fp.write("\t" + "report_reference -nosplit -hierarchy" + "\n")
        fp.write("\t" + "report_area" + "\n")
        fp.write("}\n")
        # Remove time stamp by default
        if remove_time_stamp:
            fp.write(f"exec /bin/sh -c \"sed -i 's/.*Date.*/--removed--/g' {rptf}\"\n")

    def __write_report_timing_line(self, fp, rptf, remove_time_stamp):
        fp.write("file mkdir " + os.path.dirname(rptf) + "\n")
        fp.write('redirect -file "' + rptf + '" {\n')
        fp.write("\t" + "report_timing" + "\n")
        fp.write("}\n")
        # Remove time stamp by default
        if remove_time_stamp:
            fp.write(f"exec /bin/sh -c \"sed -i 's/.*Date.*/--removed--/g' {rptf}\"\n")

    # Create a line of report_power
    def __write_report_power_line(self, fp, rptf, val, remove_time_stamp):
        fp.write("file mkdir " + os.path.dirname(rptf) + "\n")
        fp.write('redirect -file "' + rptf + '" {\n')
        fp.write("\t" + "report_power -hierarchy -levels " + str(val) + "\n")
        fp.write("}\n")
        # Remove time stamp by default
        if remove_time_stamp:
            fp.write(f"exec /bin/sh -c \"sed -i 's/.*Date.*/--removed--/g' {rptf}\"\n")

    # Create a line of check_timing
    def __write_check_timing_line(self, fp, rptf, var, remove_time_stamp):
        fp.write("file mkdir " + os.path.dirname(rptf) + "\n")
        fp.write('redirect -file "' + rptf + '" {\n')
        fp.write("\t" + var + "\n")
        fp.write("}\n")
        if remove_time_stamp:
            fp.write(f"exec /bin/sh -c \"sed -i 's/.*Date.*/--removed--/g' {rptf}\"\n")

    # Extract the variable name from a string. For example, variable ${a} -> a
    def __extract_tcl_var_name(self, var):
        ret = var
        ret = ret.lstrip("${")
        ret = ret.rstrip("}")
        return ret

    # Generate the variable with a given variable. For example, a -> ${a}
    def __tcl_var(self, var_name):
        return "${" + var_name + "}"

    # Create a line of appvar
    def __write_search_path_line(self, fp):
        search_path_val = "*"
        for db in self.__dbs_:
            search_path_val += " " + os.path.dirname(db)
        self.__write_setvar_line(fp, CMD_SEARCH_PATH, '"' + search_path_val + '"')

    # Create a line of appvar
    def __write_link_path_line(self, fp):
        link_path_val = "*"
        for db in self.__dbs_:
            link_path_val += " " + os.path.basename(db)
        self.__write_setvar_line(fp, CMD_LINK_PATH, '"' + link_path_val + '"')

    def __write_custom_recipe(self, fp, src_recipe_file):
        with open(src_recipe_file, 'r') as infile:
            # Loop through each line in the source file
            for line in infile:
                # Optional: Modify or filter the line here if needed
                fp.write(line)

    def __snps_dc_write_design_line(self, fp, val, remove_time_stamp, use_name_rule):
        # Use name rule by default:
        if use_name_rule:
            fp.write("change_names -rules verilog -hierarchy\n")
        fp.write("file mkdir " + os.path.dirname(val) + "\n")
        fp.write(f"write -format verilog -hierarchy -output {val}.v\n")
        # Remove time stamp by default
        if remove_time_stamp:
            fp.write(f"exec /bin/sh -c \"sed -i 's/.*Date.*//g' {val}.v\"\n")

    def __yosys_write_design_line(self, fp, val):
        fp.write(f"exec -- mkdir -p {os.path.dirname(val)}\n")
        fp.write(f"write_verilog -noattr {val}.v\n")
        # Remove time stamp by default
        if remove_time_stamp:
            fp.write(f"exec sed -i \"1{/^ \\\/* Generated by Yosys/d}\" {val}.v\"\n")

    def __yosys_write_techmap(self, fp):
        if len(self.__target_libs_) > 1:
            raise Exception(f"{TOOL_YOSYS} only supports single file as target technology library\n")
        if len(self.__target_libs_) == 0:
            raise Exception(f"{TOOL_YOSYS} require 1 target technology library but found 0\n")
        for var in self.__target_libs_:
            fp.write(f"dfflibmap -liberty {var}\n")
        for var in self.__target_libs_:
            fp.write(f"abc -liberty {var}\n")
        fp.write(f"clean\n")

    # Create a line of save_session
    def __write_save_session(self, fp, val):
        fp.write(f"save_session {val}\n")

    # Create a line of appvar
    def __write_exit_line(self, fp):
        fp.write("exit\n")

    # Write remove target library subset
    def __write_remove_subblock_target_library_subset(self, fp):
        fp.write("remove_target_library_subset\n")

    # def __write_source_subblock_tcl_file(self, fp, file_name):
    #     fp.write(f"source {file_name}\n")

    def __write_link(self, fp):
        fp.write("link\n")

    def __write_set_dont_touch(self, fp):
        fp.write(
            'set_dont_touch [get_cells -hierarchical -filter "ref_name == ${TARGET_DESIGN}"]\n'
        )

    def __write_rename_prefix(self, fp):
        fp.write('rename_design ${TARGET_DESIGN} -prefix "${TOP_DESIGN_NAME}_" -update_links\n')

    # Write content to a file
    def __write_for_snps_dc(self, fname):
        with open(fname, "w") as o_tcl_f:
            # Write appvar
            self.__write_comment_line(o_tcl_f, "Application Variables")
            for var in self.__appvars_.keys():
                self.__write_setvar_line(o_tcl_f, var, self.__appvars_[var])
            # Add target libs
            target_lib_appvar_val = '"' + " ".join(self.__target_libs_) + '"'
            self.__write_setvar_line(o_tcl_f, "target_library", target_lib_appvar_val)

            # Write global paths
            self.__write_comment_line(o_tcl_f, "Global paths")
            self.__write_search_path_line(o_tcl_f)
            self.__write_link_path_line(o_tcl_f)

            # Write local var
            self.__write_comment_line(o_tcl_f, "Local Variables")
            for var in self.__localvars_.keys():
                self.__write_setvar_line(o_tcl_f, var, self.__localvars_[var])
            # Read db
            self.__write_comment_line(o_tcl_f, "Read technology files")
            for var in self.__dbs_:
                self.__write_read_db_line(o_tcl_f, var)
            # Read verilog
            self.__write_comment_line(o_tcl_f, "Read design files")
            for var_idx in range(len(self.__netlists_)):
                self.__snps_dc_write_add_verilog_line(
                    o_tcl_f, self.__netlists_[var_idx], self.__netlist_types_[var_idx]
                )
            # Analyze and elaborate
            self.__write_analyze_design_line(o_tcl_f)
            self.__write_elaborate_design_line(o_tcl_f, self.__design_name_)

            # Add variables for micro floorplan synth
            self.__write_comment_line(o_tcl_f, "Variables for micro floorplan synth")
            if self.__config_group_mem_:
                self.__write_setvar_line(
                    o_tcl_f, "CONFIG_GROUP_MEM", f'"{self.__config_group_mem_}"'
                )
            if len(self.__mux_name_list_) > 0:
                mux_lst_str = ""
                for var in self.__mux_name_list_:
                    mux_lst_str += f"{var} "
                self.__write_setvar_line(o_tcl_f, "MUX_NAME_LIST", "{" + mux_lst_str + "}")
            # Define name rule for config_group_mem
            if self.__config_group_mem_:
                name_rule_str = '-map {{{"^' + str(self.__config_group_mem_) + '/",""}}}'
                o_tcl_f.write(f"define_name_rules naming_mem_cell {name_rule_str} -type cell\n")
                o_tcl_f.write(f"define_name_rules naming_mem_net {name_rule_str} -type net\n")
            for name in self.__subblocks_name_:
                comment_line = (
                    "Process sub-block " + self.__subblocks_pattern_map_[name][pattern_idx]
                )
                self.__write_comment_line(o_tcl_f, comment_line)
                if self.__subblocks_current_design_:
                    self.__write_setvar_line_priority(
                        o_tcl_f, SUBBLOCK_NAME, SUBBLOCK_CURRENT_DESIGN
                    )
                if self.__subblocks_target_design_:
                    cmd = "get_designs " + self.__subblocks_pattern_map_[name][pattern_idx]
                    self.__write_setvar_line_priority_target_design(
                        o_tcl_f, SUBBLOCK_TARGET_DESIGN, cmd
                    )
                if self.__subblocks_current_design_:
                    self.__write_subblock_current_design_target_design(o_tcl_f)
                if self.__subblocks_pattern_map_[name][flatten_idx]:
                    self.__write_flatten_line(o_tcl_f)
                self.__write_remove_subblock_target_library_subset(o_tcl_f)
                if self.__subblocks_library_subset_:
                    concate_cmd = GET_LIB_CELLS + " {" + self.__target_library_var_ + "}"
                    self.__write_setvar_target_library_subset(o_tcl_f, "-use", concate_cmd)
                if self.__subblocks_sdc_:
                    if self.__subblocks_sdc_file_name_map[name].endswith(".tcl"):
                        self.__write_source_tcl_line(
                            o_tcl_f, self.__subblocks_sdc_file_name_map[name]
                        )
                    elif self.__subblocks_sdc_file_name_map[name].endswith(".sdc"):
                        self.__write_read_sdc_line(
                            o_tcl_f, self.__subblocks_sdc_file_name_map[name]
                        )
                    else:
                        raise Exception(
                            "Invalid file format for sdc file. Expect postfix [sdc|tcl]!"
                        )

                self.__write_link(o_tcl_f)
                self.__write_custom_recipe(o_tcl_f, self.__subblock_opt_recipe_)
                self.__write_subblock_current_design_top_design_name(o_tcl_f)
                self.__write_set_dont_touch(o_tcl_f)
                if self.__subblocks_rename_prefix:
                    self.__write_rename_prefix(o_tcl_f)

            # Read sdc
            self.__write_comment_line(o_tcl_f, "Read pre-compile SDC files")
            for var in self.__sdcs_:
                if var.endswith(".tcl"):
                    self.__write_source_tcl_line(o_tcl_f, var)
                elif var.endswith(".sdc"):
                    self.__write_read_sdc_line(o_tcl_f, var)
                else:
                    raise Exception("Invalid file format for sdc file. Expect postfix [sdc|tcl]!")

            # Compile the design
            self.__write_link(o_tcl_f)
            # Write top level flatten command
            if self.__synth_task_top_flatten_:
                self.__write_flatten_line(o_tcl_f)
            self.__write_custom_recipe(o_tcl_f, self.__opt_recipe_)

            # Read post-compile sdc
            self.__write_comment_line(o_tcl_f, "Read post-compile SDC files")
            for var in self.__post_compile_sdcs_:
                if var.endswith(".tcl"):
                    self.__write_source_tcl_line(o_tcl_f, var)
                elif var.endswith(".sdc"):
                    self.__write_read_sdc_line(o_tcl_f, var)
                else:
                    raise Exception("Invalid file format for sdc file. Expect postfix [sdc|tcl]!")

            # Write synthesized netlists
            if self.__write_design_file_:
                self.__snps_dc_write_design_line(
                    o_tcl_f,
                    self.__write_design_file_,
                    self.__remove_time_stamp_,
                    self.__use_name_rule_,
                )

            # Report area
            if self.__report_area_:
                self.__write_comment_line(o_tcl_f, "Report area to file")
                self.__write_report_area_line(
                    o_tcl_f, self.__report_area_options_["file"], self.__remove_time_stamp_
                )
            if self.__report_timing_:
                self.__write_comment_line(o_tcl_f, "Report timing to file")
                self.__write_report_timing_line(
                    o_tcl_f, self.__report_timing_options_["file"], self.__remove_time_stamp_
                )

            # Report power
            if self.__report_power_:
                self.__write_comment_line(o_tcl_f, "Report power to file")
                self.__write_report_power_line(
                    o_tcl_f,
                    self.__report_power_options_["file"],
                    self.__report_power_options_["hierarchy"],
                    self.__remove_time_stamp_,
                )

            if self.__check_timing_rpt_:
                self.__write_check_timing_line(
                    o_tcl_f,
                    self.__check_timing_rpt_file_,
                    "check_timing",
                    self.__remove_time_stamp_,
                )

            # Save session
            if self.__session_name_:
                self.__write_save_session(o_tcl_f, self.__session_name_)
            # Finish
            self.__write_exit_line(o_tcl_f)

    def __write_for_yosys(self, fname):
        with open(fname, "w") as o_tcl_f:
            # Read tech libs. Only single liberty file is allowed
            self.__write_comment_line(o_tcl_f, "Read technology files")
            if len(self.__dbs_) > 1:
                raise Exception(f"{TOOL_YOSYS} only supports single file as technology library\n")
            if len(self.__dbs_) == 0:
                raise Exception(f"{TOOL_YOSYS} require 1 technology library but found 0\n")
            for var in self.__dbs_:
                self.__write_read_db_line(o_tcl_f, var)
            # Read design sources
            self.__write_comment_line(o_tcl_f, "Read design files")
            for var_idx in range(len(self.__netlists_)):
                self.__yosys_write_add_verilog_line(
                    o_tcl_f, self.__netlists_[var_idx], self.__netlist_types_[var_idx]
                )
            self.__write_elaborate_design_line(o_tcl_f, self.__design_name_)
            # Read the external file and directly add its content
            self.__write_comment_line(o_tcl_f, "Include custom synthesis recipe")
            self.__write_custom_recipe(o_tcl_f, self.__opt_recipe_)
            # Run tech map on target libs
            self.__write_comment_line(o_tcl_f, "Technology mapping")
            if self.__write_design_file_:
                self.__yosys_write_techmap(
                    o_tcl_f
                )
            # Write synthesized netlists
            self.__write_comment_line(o_tcl_f, "Write synthesized HDL design")
            if self.__write_design_file_:
                self.__yosys_write_design_line(
                    o_tcl_f,
                    self.__write_design_file_,
                    self.__remove_time_stamp_,
                )
            self.__write_comment_line(o_tcl_f, "Report")

    # Write content to a file
    def write(self, fname):
        self.__check_valid_tool()
        if self.__tool_ == TOOL_SNPS_DC:
            self.__write_for_snps_dc(fname)
        elif self.__tool_ == TOOL_YOSYS:
            self.__write_for_yosys(fname)

    # Clear all the data
    def clear(self):
        self.__init__()

    # Set config_group_mem module name
    def set_config_group_mem(self, var):
        self.__config_group_mem_ = var

    # Set list of mux module name
    def add_mux_name(self, var):
        self.__mux_name_list_.append(f'"{var}"')
