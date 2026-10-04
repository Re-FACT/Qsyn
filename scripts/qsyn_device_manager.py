import logging
import yaml
import os
from xml.dom import minidom

# Class of a Design Compiler device manager
class QsynDeviceManager:
    def __init__(self):
        # Internal data
        self.__pdk_root_ = ""
        self.__sclib_names_ = []
        self.__sclib_tags_ = []
        self.__sclib_files_ = []
        self.__is_dirty_ = True  # By default it should be dirty. After loading data and pass sanity checks, it becomes clean

    # Print a list of available standard cell libraries
    def list_sc_lib(self):
        self.__check_valid()
        logging.info(f"In total {len(self.__sclib_names_)} available standard cell library(s):")
        for sc_lib in self.__sclib_names_:
            logging.info(f"\t{sc_lib}")

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
        else:
            raise Exception("Invalid file format. Support only XML file")
        # TODO: May need a validator before flip the flag!
        self.__is_dirty_ = False

    # Clear all the data
    def clear(self):
        self.__init__()
