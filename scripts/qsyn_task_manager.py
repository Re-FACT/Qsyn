import logging
import yaml
import os

# Constants
TECH_TAG = "technology"
TECH_NAME_TAG = "name"
TECH_ROOT_TAG = "root"
TECH_CORNER_TAG = "corner"
NETLIST_TAG = "netlist"
NETLIST_INPUT_TAG = "input"
NETLIST_SYSTEM_VERILOG_FILTER_TAG = "system_verilog_filter"
NETLIST_EXCLUDE_TAG = "exclude"
NETLIST_LINK_PATH_TAG = "link_path"
NETLIST_OUTPUT_TAG = "output"
TASKS_TAG = "synth_tasks"
TASKS_NAME_TAG = "name"
TASKS_MODE_TAG = "mode"
TASKS_CURRENTDESIGN_TAG = "current_design"
TASKS_TARGETLIB_TAG = "target_library"
TASKS_SDC_TAG = "sdc"
TASKS_POST_COMPILE_SDC_TAG = "post_compile_sdc"
TASKS_COMPILE_TAG = "compile"
TASKS_COMPILE_TYPE_TAG = "type"
TASKS_COMPILE_OPT_TAG = "optimization"
TASKS_COMPILE_EFFORT_TAG = "effort"
TASKS_REMOVETIMESTAMP_TAG = "remove_time_stamp"
TASKS_NAMERULE_TAG = "name_rule"
TASKS_CHECK_TIMING_TAG = "check_timing"
TASKS_REPORTAREA_TAG = "report_area"
TASKS_REPORTAREA_FILE_TAG = "file"
TASKS_REPORTTIMING_TAG = "report_timing"
TASKS_REPORTTIMING_FILE_TAG = "file"
TASKS_REPORTPOWER_TAG = "report_power"
TASKS_REPORTPOWER_FILE_TAG = "file"
TASKS_REPORTPOWER_HIERARCHY_TAG = "hierarchy"
TASKS_SESSION_TAG = "session"
TASKS_SUBBLOCKS_TAG = "subblocks"
TASKS_SUBBLOCKS_NAME_TAG = "name"
TASKS_SUBBLOCKS_PATTERN_TAG = "pattern"
TASKS_SUBBLOCKS_FLATTEN_TAG = "flatten"
TASKS_FLATTEN_TAG = "flatten"
TASKS_CHECK_TIMING_FILE_TAG = "file"
TASKS_SUBBLOCKS_DEPENDS_TAG = "depends"
TASKS_SUBBLOCKS_COMPILE_TAG = "compile"
TASKS_SUBBLOCKS_COMPILE_TYPE_TAG = "type"
TASKS_SUBBLOCKS_COMPILE_OPTIMIZE_TAG = "optimize"
TASKS_SUBBLOCKS_COMPILE_EFFORT_TAG = "effort"
TASKS_SUBBLOCKS_TARGET_LIBRARY_OPTION_TAG = "target_library_option"
TASKS_SUBBLOCKS_TARGET_LIBRARY_SUBSET_TAG = "target_library_subset"
TASKS_SUBBLOCKS_SDC_TAG = "sdc"
TASKS_SUBBLOCKS_RENAME_PREFIX_TAG = "rename_prefix"

CURRENT_DESIGN_KEYWORD = "[current_design]"

DEVICE_DATA_MAP = {
    "sky130": "etc/device_data/sky130_constants.yml",
}


# Class of a Qsyn task manager
class QsynTaskManager:
    def __init__(self):
        # Internal data
        self.__db_ = {}
        self.__is_dirty_ = True  # By default it should be dirty. After loading data and pass sanity checks, it becomes clean
        self.__execution_order = None  # subblock order due to depends

    def __is_key_exist(self, key, path):
        if key in path:
            return True
        return False

    # get the selected device name
    def technology_name(self):
        self.__check_valid()
        return self.__db_[TECH_TAG][TECH_NAME_TAG]

    # get the selected device root dirctory
    def technology_root(self):
        self.__check_valid()
        return self.__db_[TECH_TAG][TECH_ROOT_TAG]

    # get the selected device root dirctory
    def technology_corner(self):
        self.__check_valid()
        return self.__db_[TECH_TAG][TECH_CORNER_TAG]

    def netlist_input(self):
        self.__check_valid()
        return self.__db_[NETLIST_TAG][NETLIST_INPUT_TAG]

    def netlist_exclude_files(self):
        self.__check_valid()
        if NETLIST_EXCLUDE_TAG in self.__db_[NETLIST_TAG]:
            return self.__db_[NETLIST_TAG][NETLIST_EXCLUDE_TAG]
        else:
            return []

    def netlist_system_verilog_filter(self):
        self.__check_valid()
        if NETLIST_SYSTEM_VERILOG_FILTER_TAG in self.__db_[NETLIST_TAG]:
            return self.__db_[NETLIST_TAG][NETLIST_SYSTEM_VERILOG_FILTER_TAG]
        else:
            return []

    def netlist_link_path(self):
        self.__check_valid()
        if NETLIST_LINK_PATH_TAG in self.__db_[NETLIST_TAG]:
            return self.__db_[NETLIST_TAG][NETLIST_LINK_PATH_TAG]
        else:
            return []

    def netlist_output(self):
        self.__check_valid()
        return self.__db_[NETLIST_TAG][NETLIST_OUTPUT_TAG]

    # Get the synthesis tasks
    def synth_tasks(self):
        self.__check_valid()
        if TASKS_TAG in self.__db_.keys():
            return range(len(self.__db_[TASKS_TAG]))
        return range(0)

    # Get the name of a report area task
    def synth_task_name(self, task_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_NAME_TAG]

    # Get the mode of synth task
    def synth_task_mode(self, task_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx].get(TASKS_MODE_TAG, "normal")

    # Get the design ids for a given report area task
    def synth_task_current_designs(self, task_idx):
        self.__check_valid()
        return range(len(self.__db_[TASKS_TAG][task_idx][TASKS_CURRENTDESIGN_TAG]))

    # If a task should not include time stamps
    def synth_task_remove_time_stamp(self, task_idx):
        self.__check_valid()
        if TASKS_REMOVETIMESTAMP_TAG in self.__db_[TASKS_TAG][task_idx]:
            return self.__db_[TASKS_TAG][task_idx][TASKS_REMOVETIMESTAMP_TAG]
        return True

    # If a task should not include a custom name rule
    def synth_task_use_name_rule(self, task_idx):
        self.__check_valid()
        if TASKS_NAMERULE_TAG in self.__db_[TASKS_TAG][task_idx]:
            return self.__db_[TASKS_TAG][task_idx][TASKS_NAMERULE_TAG]
        return True

    def synth_task_check_timing(self, task_idx):
        self.__check_valid()
        return TASKS_CHECK_TIMING_TAG in self.__db_[TASKS_TAG][task_idx]

    # Check a task timing rpt
    def synth_task_get_check_timing_rpt(self, task_idx, design_idx):
        self.__check_valid()
        check_timing_tag = self.__db_[TASKS_TAG][task_idx].get(TASKS_CHECK_TIMING_TAG, "")
        if check_timing_tag:
            fname = os.path.abspath(
                self.__db_[TASKS_TAG][task_idx][TASKS_CHECK_TIMING_TAG][TASKS_CHECK_TIMING_FILE_TAG]
            )
            fname = fname.replace(
                CURRENT_DESIGN_KEYWORD, self.synth_task_current_design(task_idx, design_idx)
            )
            return fname
        return ""

    # Get the design name for a given report area task
    def synth_task_current_design(self, task_idx, design_idx):
        self.__check_valid()
        if design_idx < len(self.__db_[TASKS_TAG][task_idx][TASKS_CURRENTDESIGN_TAG]):
            return self.__db_[TASKS_TAG][task_idx][TASKS_CURRENTDESIGN_TAG][design_idx]
        raise Exception(
            f"Design index '{design_idx}' is out of range [0, {len(self.synth_task_current_designs(task_idx))})!"
        )

    # Get the design name for a given report area task
    def synth_task_target_library(self, task_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_TARGETLIB_TAG]

    # Get subblocks from yaml file
    def synth_task_subblocks(self, task_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx].get(TASKS_SUBBLOCKS_TAG, "")

    # Get subblocks name from yaml file
    def synth_task_subblocks_name(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_NAME_TAG
        ]

    # Get subblocks pattern from yaml file
    def synth_task_subblocks_pattern(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_PATTERN_TAG
        ]

    # Get subblocks flatten from yaml file
    def synth_task_subblocks_flattern(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx].get(
            TASKS_SUBBLOCKS_FLATTEN_TAG, False
        )

    # Get synth task flatten from yaml file
    def synth_task_top_flattern(self, task_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx].get(TASKS_FLATTEN_TAG, False)

    # Get subblocks depends form yaml file
    def synth_task_subblocks_depends(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx].get(
            TASKS_SUBBLOCKS_DEPENDS_TAG, []
        )

    # Get subblocks compile from yaml file
    def synth_task_subblocks_compile(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_COMPILE_TAG
        ]

    # Get subblocks compile type from yaml file
    def synth_task_subblocks_compile_type(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_COMPILE_TAG
        ][TASKS_SUBBLOCKS_COMPILE_TYPE_TAG]

    # Get subblocks compile optimize from yaml file
    def synth_task_subblocks_compile_optimize(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_COMPILE_TAG
        ][TASKS_SUBBLOCKS_COMPILE_OPTIMIZE_TAG]

    # Get subblocks compile effort from yaml file
    def synth_task_subblocks_compile_effort(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_COMPILE_TAG
        ][TASKS_SUBBLOCKS_COMPILE_EFFORT_TAG]

    # Get subblocks compile effort from yaml file
    def synth_task_subblocks_target_library_option(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_TARGET_LIBRARY_OPTION_TAG
        ]

    # Get subblocks compile effort from yaml file
    def synth_task_subblocks_target_library_subset(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_TARGET_LIBRARY_SUBSET_TAG
        ]

    # Get subblocks sdc file
    def synth_task_subblocks_sdc(self, task_idx, subblocks_idx):
        self.__check_valid()
        subblock_sdc_list = []
        if (
            TASKS_SUBBLOCKS_SDC_TAG
            in self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx]
        ):
            for sdc_f in self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
                TASKS_SUBBLOCKS_SDC_TAG
            ]:
                subblock_sdc_list.append(os.path.join(os.getcwd(), sdc_f))
        return subblock_sdc_list

    # Get subblocks rename_prefix
    def synth_task_subblocks_rename_prefix(self, task_idx, subblocks_idx):
        self.__check_valid()
        return self.__db_[TASKS_TAG][task_idx][TASKS_SUBBLOCKS_TAG][subblocks_idx][
            TASKS_SUBBLOCKS_RENAME_PREFIX_TAG
        ]

    # Get the design name for a given report area task
    def synth_task_save_session(self, task_idx):
        self.__check_valid()
        return TASKS_SESSION_TAG in self.__db_[TASKS_TAG][task_idx]

    # Get the design name for a given report area task
    def synth_task_session_name(self, task_idx, design_idx):
        self.__check_valid()
        return (
            self.__db_[TASKS_TAG][task_idx][TASKS_SESSION_TAG]
            + "_"
            + self.synth_task_current_design(task_idx, design_idx)
        )

    # Get the sdc file to be loaded before running compilation
    def synth_task_sdc(self, task_idx):
        self.__check_valid()
        sdc_list = []
        if TASKS_SDC_TAG in self.__db_[TASKS_TAG][task_idx]:
            for sdc_f in self.__db_[TASKS_TAG][task_idx][TASKS_SDC_TAG]:
                sdc_list.append(os.path.join(os.getcwd(), sdc_f))
        return sdc_list

    # Get the sdc file to be loaded after running compilation
    def synth_task_post_compile_sdc(self, task_idx):
        self.__check_valid()
        sdc_list = []
        if TASKS_POST_COMPILE_SDC_TAG in self.__db_[TASKS_TAG][task_idx]:
            for sdc_f in self.__db_[TASKS_TAG][task_idx][TASKS_POST_COMPILE_SDC_TAG]:
                sdc_list.append(os.path.join(os.getcwd(), sdc_f))
        return sdc_list

    # Get if the current synthesis task require a stage of compilation
    def synth_task_require_compile(self, task_idx):
        self.__check_valid()
        return TASKS_COMPILE_TAG in self.__db_[TASKS_TAG][task_idx]

    # Get the compilation type, optimization objective and effort level
    def synth_task_compile_type(self, task_idx):
        self.__check_valid()
        if TASKS_COMPILE_TAG in self.__db_[TASKS_TAG][task_idx]:
            if TASKS_COMPILE_TYPE_TAG in self.__db_[TASKS_TAG][task_idx][TASKS_COMPILE_TAG]:
                return self.__db_[TASKS_TAG][task_idx][TASKS_COMPILE_TAG][TASKS_COMPILE_TYPE_TAG]
        return "ultra"

    def synth_task_compile_optimization(self, task_idx):
        self.__check_valid()
        if TASKS_COMPILE_TAG in self.__db_[TASKS_TAG][task_idx]:
            if TASKS_COMPILE_OPT_TAG in self.__db_[TASKS_TAG][task_idx][TASKS_COMPILE_TAG]:
                return self.__db_[TASKS_TAG][task_idx][TASKS_COMPILE_TAG][TASKS_COMPILE_OPT_TAG]
        return "balanced"

    def synth_task_compile_effort(self, task_idx):
        self.__check_valid()
        if TASKS_COMPILE_TAG in self.__db_[TASKS_TAG][task_idx]:
            if TASKS_COMPILE_EFFORT_TAG in self.__db_[TASKS_TAG][task_idx][TASKS_COMPILE_TAG]:
                return self.__db_[TASKS_TAG][task_idx][TASKS_COMPILE_TAG][TASKS_COMPILE_EFFORT_TAG]
        return "high"

    # Get the sdc file to be pre-loaded brefore running actual report_timing for a given report timing task
    def synth_task_report_area(self, task_idx):
        self.__check_valid()
        return TASKS_REPORTAREA_TAG in self.__db_[TASKS_TAG][task_idx]

    def synth_task_report_area_file(self, task_idx, design_idx):
        self.__check_valid()
        if self.__db_[TASKS_TAG][task_idx][TASKS_REPORTAREA_TAG]:
            # Replace keywords
            fname = os.path.abspath(
                self.__db_[TASKS_TAG][task_idx][TASKS_REPORTAREA_TAG][TASKS_REPORTAREA_FILE_TAG]
            )
            fname = fname.replace(
                CURRENT_DESIGN_KEYWORD, self.synth_task_current_design(task_idx, design_idx)
            )
            return fname
        return ""

    def synth_task_report_timing(self, task_idx):
        self.__check_valid()
        return TASKS_REPORTTIMING_TAG in self.__db_[TASKS_TAG][task_idx]

    def synth_task_report_timing_file(self, task_idx, design_idx):
        self.__check_valid()
        if self.__db_[TASKS_TAG][task_idx][TASKS_REPORTTIMING_TAG]:
            fname = os.path.abspath(
                self.__db_[TASKS_TAG][task_idx][TASKS_REPORTTIMING_TAG][TASKS_REPORTTIMING_FILE_TAG]
            )
            fname = fname.replace(
                CURRENT_DESIGN_KEYWORD, self.synth_task_current_design(task_idx, design_idx)
            )
            return fname
        return ""

    def synth_task_report_power(self, task_idx):
        self.__check_valid()
        return TASKS_REPORTPOWER_TAG in self.__db_[TASKS_TAG][task_idx]

    def synth_task_report_power_file(self, task_idx, design_idx):
        self.__check_valid()
        if self.__db_[TASKS_TAG][task_idx][TASKS_REPORTPOWER_TAG]:
            fname = os.path.abspath(
                self.__db_[TASKS_TAG][task_idx][TASKS_REPORTPOWER_TAG][TASKS_REPORTPOWER_FILE_TAG]
            )
            fname = fname.replace(
                CURRENT_DESIGN_KEYWORD, self.synth_task_current_design(task_idx, design_idx)
            )
            return fname
        return ""

    def synth_task_report_power_hierarchy(self, task_idx):
        self.__check_valid()
        if TASKS_REPORTPOWER_TAG in self.__db_[TASKS_TAG][task_idx]:
            if (
                TASKS_REPORTPOWER_HIERARCHY_TAG
                in self.__db_[TASKS_TAG][task_idx][TASKS_REPORTPOWER_TAG]
            ):
                return self.__db_[TASKS_TAG][task_idx][TASKS_REPORTPOWER_TAG][
                    TASKS_REPORTPOWER_HIERARCHY_TAG
                ]
        return 1

    # Internal method to check if data is valid, throw exeception when invalid. Useful for accessors
    def __check_valid(self):
        if self.__is_dirty_ == True:
            raise Exception("Try to access data when internal data is still dirty. Load data first")

    def is_valid(self):
        return not (self.__is_dirty_)

    # Load data from yaml file
    def load(self, yaml_filename):
        self.__db_ = {}  # Ensure a clean start
        with open(yaml_filename, "r") as stream:
            try:
                self.__db_ = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                logging.error(exc)
        # TODO: May need a validator before flip the flag!
        self.__is_dirty_ = False

    # Clear all the data
    def clear(self):
        self.__init__()
