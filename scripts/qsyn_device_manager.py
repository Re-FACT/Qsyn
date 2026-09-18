import logging
import yaml
import os
from xml.dom import minidom

# Constants
PDK_TAG = "pdk"
PDK_HOME_TAG = "home"
PDK_ROOT_TAG = "root"
PDK_NLDM_TAG = "nldm"
PDK_NLDM_ROOT_TAG = "root"
PDK_NLDM_VERSION_TAG = "version"
PDK_NLDM_FILETYPE_TAG = "file_type"
PDK_NLDM_PATHTEMPLATES_TAG = "path_templates"
SCLIB_TAG = "sc_lib"
SCLIB_VARS_TAG = "vars"
SCLIB_PATH_TAG = "path"
SCLIB_REQCORNER_TAG = "require_corner"
CORNERNAMES_TAG = "corner_names"
CORNERNAMES_PVT_TAG = "pvt"
CORNERNAMES_RC_TAG = "rc"
CORNERNAMES_BRAM_TAG = "bram"

# Constants
NLDM_FILE_POSTFIX = ".db"

# Keywords
CURRENT_CORNER_KEYWORD = "[current_corner]"
CURRENT_VERSION_KEYWORD = "[current_version]"
CURRENT_FILETYPE_KEYWORD = "[current_file_type]"


# Class of a Design Compiler device manager
class QsynDeviceManager:
    def __init__(self):
        # Internal data
        self.__pdk_root_ = ""
        self.__sclib_names_ = []
        self.__sclib_tags_ = []
        self.__sclib_files_ = []
        self.__is_dirty_ = True  # By default it should be dirty. After loading data and pass sanity checks, it becomes clean

    def __replace_pdk_reserved_words(self, yaml_db, fname, pvt_corner):
        temp_fname = fname
        temp_fname = temp_fname.replace(
            CURRENT_FILETYPE_KEYWORD, yaml_db[PDK_TAG][PDK_NLDM_TAG][PDK_NLDM_FILETYPE_TAG]
        )
        temp_fname = temp_fname.replace(
            CURRENT_VERSION_KEYWORD, yaml_db[PDK_TAG][PDK_NLDM_TAG][PDK_NLDM_VERSION_TAG]
        )
        temp_fname = temp_fname.replace(
            CURRENT_CORNER_KEYWORD, yaml_db[CORNERNAMES_TAG][pvt_corner][CORNERNAMES_PVT_TAG]
        )
        return temp_fname

    def __replace_sclib_local_vars(self, yaml_db, fname, sc_lib):
        # Walk through all the variables defined under the vars section of the given sc_lib
        # Create keyword to replace
        temp_fname = fname
        for curr_var in yaml_db[SCLIB_TAG][sc_lib][SCLIB_VARS_TAG].keys():
            curr_kw = "[current_" + curr_var + "]"
            temp_fname = temp_fname.replace(
                curr_kw, yaml_db[SCLIB_TAG][sc_lib][SCLIB_VARS_TAG][curr_var]
            )
        return temp_fname

    # Print a list of available standard cell libraries
    def list_sc_lib(self):
        self.__check_valid()
        logging.info(f"In total {len(self.__sclib_names_)} available standard cell library(s):")
        for sc_lib in self.__sclib_names_:
            logging.info(f"\t{sc_lib}")

    def __sc_lib_require_corner(self, yaml_db, sc_lib):
        if SCLIB_REQCORNER_TAG not in yaml_db[SCLIB_TAG][sc_lib]:
            return yaml_db[CORNERNAMES_TAG].keys()  # Return all the defined corners by default
        return yaml_db[SCLIB_TAG][sc_lib][SCLIB_REQCORNER_TAG]

    # Infer a list of the file names representing standard cell library
    def standard_cell_libs(self, root_dir, pvt_corner):
        self.__check_valid()
        root_abspath = os.path.abspath(self.__pdk_root_)
        if root_dir:
            root_abspath = os.path.abspath(root_dir)
        sc_libs = []
        for ilib in range(len(self.__sclib_names_)):
            if pvt_corner != self.__sclib_tags_[ilib]:
                continue
            sc_libs.append(os.path.join(root_abspath, self.__sclib_files_[ilib]))
        return sc_libs

    # Get the file name representing standard cell library with a given tag
    def find_standard_cell_library_by_tag(self, root_dir, pvt_corner, sc_lib_tag):
        self.__check_valid()
        root_abspath = os.path.abspath(self.__pdk_root_)
        if root_dir:
            root_abspath = os.path.abspath(root_dir)
        for ilib in range(len(self.__sclib_names_)):
            if sc_lib_tag != self.__sclib_names_[ilib]:
                continue
            if pvt_corner != self.__sclib_tags_[ilib]:
                continue
            return os.path.join(root_abspath, self.__sclib_files_[ilib])
        return ""

    # Internal method to check if data is valid, throw exeception when invalid. Useful for accessors
    def __check_valid(self):
        if self.__is_dirty_ == True:
            raise Exception("Try to access data when internal data is still dirty. Load data first")

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
        # Parse db
        self.__pdk_root_ = yaml_db[PDK_TAG][PDK_ROOT_TAG]
        # For each sclibs
        self.__sclib_names_ = []
        self.__sclib_tags_ = []
        self.__sclib_files_ = []
        pdk_home = yaml_db[PDK_TAG][PDK_HOME_TAG]
        pdk_nldm_root = yaml_db[PDK_TAG][PDK_NLDM_TAG][PDK_NLDM_ROOT_TAG]
        for sc_lib in yaml_db[SCLIB_TAG].keys():
            # Filter out sc_lib that does not support the selected pvt_corner
            template_name = yaml_db[SCLIB_TAG][sc_lib][SCLIB_PATH_TAG]
            if (
                template_name
                not in yaml_db[PDK_TAG][PDK_NLDM_TAG][PDK_NLDM_PATHTEMPLATES_TAG].keys()
            ):
                raise Exception(
                    f"Template '{template_name}' given at '{sc_lib}' of sc_lib section is not a valid one under the path templates '{template_name}' of ndlm section"
                )
            sc_lib_fname = yaml_db[PDK_TAG][PDK_NLDM_TAG][PDK_NLDM_PATHTEMPLATES_TAG][template_name]
            for pvt_corner in self.__sc_lib_require_corner(yaml_db, sc_lib):
                sc_lib_fname = self.__replace_pdk_reserved_words(yaml_db, sc_lib_fname, pvt_corner)
                sc_lib_fname = self.__replace_sclib_local_vars(yaml_db, sc_lib_fname, sc_lib)
                sc_lib_full_path = os.path.join(pdk_home, pdk_nldm_root, sc_lib_fname)
                self.__sclib_names_.append(sc_lib)
                self.__sclib_tags_.append(pvt_corner)
                self.__sclib_files_.append(sc_lib_full_path)

    # Load data from xml file
    def __load_from_xml(self, xml_filename):
        xml_db = minidom.parse(xml_filename)
        if xml_db.documentElement.tagName != "pdk":
            raise Exception(
                f"Expect the root node of XML to be 'pdk'! Currently it is '{xml_db.documentElement.tagName}'"
            )
        # Parse pdk root path
        pdk_root_node = xml_db.getElementsByTagName("root")
        if len(pdk_root_node) == 0:
            raise Exception(f"Expect the pdk root node of XML to be defined!")
        if len(pdk_root_node) != 1:
            raise Exception(f"Expect only 1 pdk root node of XML to be defined!")
        self.__pdk_root_ = pdk_root_node[0].firstChild.data
        # Parse sclibs
        sclibs_node = xml_db.getElementsByTagName("sclibs")
        if len(sclibs_node) == 0:
            raise Exception(f"Expect the sclibs node of XML to be defined!")
        if len(sclibs_node) != 1:
            raise Exception(f"Expect only 1 sclibs node of XML to be defined!")
        sclibs_node = sclibs_node[0].getElementsByTagName("sclib")
        for sclib_node in sclibs_node:
            lib_name = sclib_node.attributes["name"].value
            # Get each file with tag
            files_node = sclib_node.getElementsByTagName("file")
            for file_node in files_node:
                lib_tag = file_node.attributes["tag"].value
                lib_fname = file_node.firstChild.data
                self.__sclib_names_.append(lib_name)
                self.__sclib_tags_.append(lib_tag)
                self.__sclib_files_.append(lib_fname)

    def load(self, fname):
        if fname.endswith(".xml"):
            self.__load_from_xml(fname)
        elif fname.endswith(".yaml") or fname.endswith(".yml"):
            self.__load_from_yaml(fname)
        else:
            raise Exception("Invalid file format. Support only YAML and XML file")
        # TODO: May need a validator before flip the flag!
        self.__is_dirty_ = False

    # Clear all the data
    def clear(self):
        self.__init__()
