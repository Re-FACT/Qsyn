import logging
import yaml
import os

# Constants


# Class of a PTPX task manager
class ConfigMemManager:
    def __init__(self):
        # Internal data
        self.__db_ = {}
        self.__is_dirty_ = True  # By default it should be dirty. After loading data and pass sanity checks, it becomes clean

    def __is_key_exist(self, key, path):
        if key in path:
            return True
        return False

    # Add variables for micro floorplan synth
    def config_group_mem(self, design_name):
        self.__check_valid()
        if design_name in self.__db_:
            if len(self.__db_[design_name]) != 1:
                raise Exception(
                    f"Invalid configuration memory group. Expect only 1 memory group under '{design_name}'!"
                )
            return self.__db_[design_name][0]
        return ""

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
