import logging
import yaml
import os

# Constants
BIN_TAG = "bin"
OPTIONS_TAG = "options"
PARGS_TAG = "pargs"
PARGS_NAME_TAG = "name"
KARGS_TAG = "kargs"
KARGS_NAME_TAG = "name"

# Constants
# Keywords
TCL_KEYWORD = "[tcl]"

# Class of a tool manager
class QsynToolManager:
    def __init__(self):
        # Internal data
        self.__db_ = {}
        self.__is_dirty_ = True  # By default it should be dirty. After loading data and pass sanity checks, it becomes clean

    def list_tools(self):
        self.__check_valid()
        logging.info(f"In total {len(self.__db_.keys())} available synthesis tool(s):")
        for tool in self.__db_.keys():
            logging.info(f"\tTool: {tool}")

    def __valid_tool(self, tool):
        if tool not in self.__db_.keys():
            raise Exception(
                f"Tool '{tool}' is not defined in the tool configuration file!\n{self.list_tools()}\n"
            )

    def binary_path(self, tool):
        self.__valid_tool(tool)
        if BIN_TAG not in self.__db_[tool]:
            raise Exception(
                f"Required syntax '{BIN_TAG}' is not defined under tool '{tool}' in the tool configuration file!\n"
            )
        return self.__db_[task_type][BIN_TAG]

    def __tool_pargs(self, tool, cust_args):
        if PARGS_TAG not in self.__db_[tool]:
            raise Exception(
                f"Required syntax '{PARGS_TAG}' is not defined under tool '{tool}' in the tool configuration file!\n"
            )
        arg_str = ""
        for parg_idx in range(len(self.__db_[tool][PARGS_TAG])):
            if PARGS_NAME_TAG not in self.__db_[tool][PARGS_TAG][parg_idx]:
                raise Exception(
                    f"Required syntax '{PARGS_NAME_TAG}' of '{PARGS_TAG}' is not defined under tool '{tool}' in the tool configuration file!\n"
                )
            parg_pattern = self.__db_[tool][PARGS_TAG][parg_idx][PARGS_NAME_TAG]
            for cust_arg in cust_args.keys():
                cust_arg_pattern = cust_arg
                if cust_arg_pattern not in parg_pattern:
                    continue
                for cust_arg_val in cust_args[cust_arg]:
                    arg_str += " " + parg_pattern.replace(cust_arg_pattern, cust_arg_val)
        return arg_str

    def __tool_kargs(self, tool, cust_args):
        if KARGS_TAG not in self.__db_[tool]:
            raise Exception(
                f"Required syntax '{KARGS_TAG}' is not defined under tool '{tool}' in the tool configuration file!\n"
            )
        arg_str = ""
        for karg_idx in range(len(self.__db_[tool][KARGS_TAG])):
            if KARGS_NAME_TAG not in self.__db_[tool][KARGS_TAG][karg_idx]:
                raise Exception(
                    f"Required syntax '{KARGS_NAME_TAG}' of '{KARGS_TAG}' is not defined under tool '{tool}' in the tool configuration file!\n"
                )
            karg_pattern = self.__db_[tool][KARGS_TAG][karg_idx][KARGS_NAME_TAG]
            karg_appended = False
            for cust_arg in cust_args.keys():
                cust_arg_pattern = cust_arg
                if cust_arg_pattern not in karg_pattern:
                    continue
                for cust_arg_val in cust_args[cust_arg]:
                    arg_str += " " + karg_pattern.replace(cust_arg_pattern, cust_arg_val)
                    karg_appended = True
            if not karg_appended:
                arg_str += " " + karg_pattern
        return arg_str

    def tool_args(self, tool, cust_args):
        self.__valid_tool(tool)
        # Get options
        if OPTIONS_TAG not in self.__db_[tool]:
            raise Exception(
                f"Required syntax '{OPTIONS_TAG}' is not defined under tool '{tool}' in the tool configuration file!\n"
            )
        # Check options format
        arg_str = ""
        for opt_type in self.__db_[tool][OPTIONS_TAG].split(" "):
            if opt_type != PARGS_TAG and opt_type != KARGS_TAG:
                raise Exception(
                    f"Invalid option format '{self.__db_[task_type][OPTIONS_TAG]}' is not valid under tool '{tool}' in the tool configuration file! Expect [{PARGS_TAG}|{KARGS_TAG}]\n"
                )
            if opt_type == PARGS_TAG:
                arg_str += self.__tool_pargs(tool, cust_args)
            elif opt_type == KARGS_TAG:
                arg_str += self.__tool_kargs(tool, cust_args)
        return arg_str

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
