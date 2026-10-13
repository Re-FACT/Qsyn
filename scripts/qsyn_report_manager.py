import logging
import yaml
import os
import csv
import json

# Constants: unified metic names
TOTAL_CELL_AREA_TAG = "total_cell_area"
NUM_CELLS_TAG = "num_cells"
AREA_TAGS = [TOTAL_CELL_AREA_TAG, NUM_CELLS_TAG]
# Constants for DC-style reports
SNPS_DC_TOTAL_CELL_AREA_TAG = "Total cell area:"
SNPS_DC_NUM_CELLS_TAG = "Number of cells:"
SNPS_DC_AREA_TAGS = {
  TOTAL_CELL_AREA_TAG: SNPS_DC_TOTAL_CELL_AREA_TAG,
  NUM_CELLS_TAG : SNPS_DC_NUM_CELLS_TAG,
}
# Constants for yosys-style reports
YOSYS_TOTAL_CELL_AREA_TAG = "area"
YOSYS_NUM_CELLS_TAG = "num_cells"
YOSYS_AREA_TAGS = {
  TOTAL_CELL_AREA_TAG : YOSYS_TOTAL_CELL_AREA_TAG,
  NUM_CELLS_TAG : YOSYS_NUM_CELLS_TAG,
}

# Class of a DC report manager
class QsynReportManager:
    def __init__(self):
        # Internal data
        self.__syn_design_names_ = []
        self.__syn_tools_ = []
        self.__syn_area_report_files_ = []
        self.__syn_timing_report_files_ = []
        self.__syn_power_report_files_ = []
        self.__rpt_db_ = {}  # nested dict: [design_name][metric]
        self.__error_count_ = 0  # Flag DC run is successfully or not
        # Constants
        # TODO: Loaded from a method? Avoid duplicated definition in qsyn_tcl_writer.py
        self.__SNPS_DC_TOOL_NAME_ = "snps_dc"
        self.__YOSYS_TOOL_NAME_ = "yosys"
        self.__SUPPORTED_TOOLS_ = [ self.__SNPS_DC_TOOL_NAME_, self.__YOSYS_TOOL_NAME_ ]

    def add_area_report_file(self, val, design_name, tool_name):
        # Should have a valid name
        if tool_name not in self.__SUPPORTED_TOOLS_:
            raise Exception(f"Invalid tool name '{tool_name}'. Expect one of the following: {self.__SUPPORTED_TOOLS_}")
        if design_name in self.__syn_design_names_:
            design_idx = self.__syn_design_names_.index(design_name)
            self.__syn_area_report_files_[design_idx] = val
            self.__syn_tools_ = tool_name
        else:
            self.__syn_design_names_.append(design_name)
            self.__syn_area_report_files_.append(val)
            self.__syn_tools_.append(tool_name)
            self.__syn_timing_report_files_.append("")
            self.__syn_power_report_files_.append("")

    # Parses a Yosys JSON file and extracts the 'area' value from the 'design' section.
    def __parse_yosys_area_report(self, rpt_file, design_name):
        try:
            with open(rpt_file, 'r') as jfile:
                data: Dict[str, Any] = json.load(jfile)
                
            # Safely access the design section and the area key
            raw_num_cells = data.get("design", {}).get("num_cells")
            # Assign to area
            for curr_unified_tag, curr_ys_tag in YOSYS_AREA_TAGS:
                raw_area_data = data.get("design", {}).get(curr_ys_tag)
                if not design_name in self.__rpt_db_:
                    self.__rpt_db_[design_name] = {}
                self.__rpt_db_[design_name][curr_unified_tag] = float(raw_area_data)
        except FileNotFoundError:
            print(f"Error: The file '{rpt_file}' was not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from '{rpt_file}'. Check if the file format is valid.")
            return None

    # Parse an area report: extract data by matching the metric names
    def __parse_snps_dc_area_report(self, rpt_file, design_name):
        with open(rpt_file, "r") as rptf:
            for line in rptf:
                # Chomp empty spaces
                processed_line = line.lstrip()
                processed_line = processed_line.rstrip()
                # Start keyword matching
                for curr_unified_tag, curr_dc_tag in SNPS_DC_AREA_TAGS:
                    if processed_line.startswith(curr_dc_tag):
                        data_line = processed_line.removeprefix(curr_dc_tag)
                        data_line = data_line.lstrip()
                        if not design_name in self.__rpt_db_:
                            self.__rpt_db_[design_name] = {}
                        self.__rpt_db_[design_name][curr_unified_tag] = data_line
            rptf.close()

    # Walk through each report file, design by design. And extract data by matching the metric names
    def __parse_area_reports(self):
        for design_idx in range(len(self.__syn_design_names_)):
            rpt_fpath = self.__syn_area_report_files_[design_idx]
            syn_dsgn_name = self.__syn_design_names_[design_idx]
            if self.__syn_tools_[design_idx] == self.__SNPS_DC_TOOL_NAME_ :
                self.__parse_snps_dc_area_report(rpt_fpath, syn_dsgn_name)
            if self.__syn_tools_[design_idx] == self.__YOSYS_TOOL_NAME_ :
                self.__parse_yosys_area_report(rpt_fpath, syn_dsgn_name)

    # Output the parse results to a summary file
    def write_report_summary(self, sum_file):
        # parse the report
        self.__parse_area_reports()
        # write to file
        os.makedirs(os.path.dirname(os.path.abspath(sum_file)), exist_ok=True)
        with open(sum_file, "w") as sumf:
            spamwriter = csv.writer(sumf, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            # Write head lines
            spamwriter.writerow(["Design Name"] + AREA_TAGS)
            # Write data of designs one by one
            for design_name in self.__dc_design_names_:
                row_data = [design_name]
                for curr_tag in AREA_TAGS:
                    row_data.append(self.__rpt_db_[design_name][curr_tag])
                spamwriter.writerow(row_data)

    # Clear all the data
    def clear(self):
        self.__init__()
