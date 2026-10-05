import logging
import yaml
import os
from xml.dom import minidom

# Constants
REG_TASK_TAG = "reg_tasks"
REG_TASK_NAME_TAG = "name"
REG_TASK_WORKSPACE_TAG = "workspace"
REG_TASK_CMD_TAG = "command"
REG_TASK_DEP_TAG = "depend"
REG_TASK_EXPECT_FAILURE_TAG = "expect_failure"

class EzRegTaskManager:
    def __init__(self):
        # Internal data
        self.__task_names_ = []
        self.__task_workspaces_ = []
        self.__task_commands_ = []
        self.__task_dependencies_ = []
        self.__task_expect_failures_ = []
        self.__is_dirty_ = True  # By default it should be dirty. After loading data and pass sanity checks, it will be flipped to clean
        self.__EXPECT_FAILURE_STRING_ = {"true": True, "false": False}

    def empty(self):
        return len(self.__task_names_) == 0

    # Internal method to check if data is valid, throw exeception when invalid. Useful for accessors
    def __check_valid(self):
        if self.__is_dirty_ == True:
            raise Exception("Try to access data when internal data is still dirty. Load data first")

    def num_tasks(self):
        self.__check_valid()
        return len(self.__task_names_)

    def tasks(self):
        self.__check_valid()
        return range(len(self.__task_names_))

    def __valid_task(self, task_idx):
        if task_idx not in self.tasks():
            raise Exception(f"Invalid task id {task_idx}")

    def task_name(self, task_idx):
        self.__check_valid()
        self.__valid_task(task_idx)
        return self.__task_names_[task_idx]

    def task_workspace(self, task_idx):
        self.__check_valid()
        self.__valid_task(task_idx)
        return self.__task_workspaces_[task_idx]

    def task_command(self, task_idx):
        self.__check_valid()
        self.__valid_task(task_idx)
        return self.__task_commands_[task_idx]

    def task_dependency(self, task_idx):
        self.__check_valid()
        self.__valid_task(task_idx)
        return self.__task_dependencies_[task_idx]

    def task_expect_failure(self, task_idx):
        self.__check_valid()
        self.__valid_task(task_idx)
        return self.__task_expect_failures_[task_idx]

    def is_valid(self):
        return not (self.__is_dirty_)

    # Load data from yaml file
    def __load_from_yaml(self, yaml_filename):
        yaml_db = {}
        with open(yaml_filename, "r") as stream:
            try:
                yaml_db = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                logging.error(exc)
        # For each sclibs
        self.__task_names_ = []
        self.__task_workspaces_ = []
        self.__task_dependencies_ = []
        for itask in range(len(yaml_db[TASK_TAG])):
            task_name = yaml_db[TASK_TAG][itask][TASK_NAME_TAG]
            task_wkspace = yaml_db[TASK_TAG][itask][TASK_WORKSPACE_TAG]
            task_cmd = yaml_db[TASK_TAG][itask][TASK_CMD_TAG]
            task_deps = []
            if TASK_DEP_TAG in yaml_db[TASK_TAG][itask]:
                task_deps = yaml_db[TASK_TAG][itask][TASK_DEP_TAG]
            task_expect_failure = False
            if TASK_EXPECT_FAILURE_TAG in yaml_db[TASK_TAG][itask]:
                task_expect_failure = yaml_db[TASK_TAG][itask][TASK_EXPECT_FAILURE_TAG]
            self.__task_names_.append(task_name)
            self.__task_workspaces_.append(task_wkspace)
            self.__task_commands_.append(task_cmd)
            self.__task_dependencies_.append(task_deps)
            self.__task_expect_failures_.append(task_expect_failure)

    def __valid_dep(self, dep_name):
        for itask in range(len(self.__task_names_)):
            if dep_name == self.__task_names_[itask]:
                return True
        return False

    def load(self, fname):
        if fname.endswith(".yaml") or fname.endswith(".yml"):
            self.__load_from_yaml(fname)
        else:
            raise Exception("Invalid file format. Support only YAML and XML file")
        # Validate all the deps
        for itask in range(len(self.__task_names_)):
            for dep_name in self.__task_dependencies_[itask]:
                if dep_name == self.__task_names_[itask]:
                    raise Exception(
                        f"Task '{self.__task_names_[itask]}' cannot have a dependency on itself!\n"
                    )
                if not self.__valid_dep(dep_name):
                    raise Exception(
                        f"Dependency '{dep_name}' of task '{self.__task_names_[itask]}' is not a valid task name!\n"
                    )

        # TODO: May need a validator before flip the flag!
        self.__is_dirty_ = False

    # Clear all the data
    def clear(self):
        self.__init__()
