import logging
import yaml
import os
import csv

# Constants
TOTAL_CELL_AREA_TAG = "Total cell area:"
NUM_CELLS_TAG = "Number of cells:"
AREA_TAGS = [TOTAL_CELL_AREA_TAG, NUM_CELLS_TAG]


# Class of a DC report manager
class QsynReportManager:
    def __init__(self):
        # Internal data
        self.__dc_design_names_ = []
        self.__dc_area_report_files_ = []
        self.__dc_timing_report_files_ = []
        self.__dc_power_report_files_ = []
        self.__rpt_db_ = {}  # nested dict: [design_name][metric]
        self.__error_count_ = 0  # Flag DC run is successfully or not

    def add_area_report_file(self, val, design_name):
        if design_name in self.__dc_design_names_:
            design_idx = self.__dc_design_names_.index(design_name)
            self.__dc_area_report_files_[design_idx] = val
        else:
            self.__dc_design_names_.append(design_name)
            self.__dc_area_report_files_.append(val)
            self.__dc_timing_report_files_.append("")
            self.__dc_power_report_files_.append("")

    # Parse an area report: extract data by matching the metric names
    def __parse_area_report(self, rpt_file, design_name):
        with open(rpt_file, "r") as rptf:
            for line in rptf:
                # Chomp empty spaces
                processed_line = line.lstrip()
                processed_line = processed_line.rstrip()
                # Start keyword matching
                for curr_tag in AREA_TAGS:
                    if processed_line.startswith(curr_tag):
                        data_line = processed_line.removeprefix(curr_tag)
                        data_line = data_line.lstrip()
                        if not design_name in self.__rpt_db_:
                            self.__rpt_db_[design_name] = {}
                        self.__rpt_db_[design_name][curr_tag] = data_line
            rptf.close()

    # Walk through each report file, design by design. And extract data by matching the metric names
    def __parse_area_reports(self):
        for design_idx in range(len(self.__dc_design_names_)):
            self.__parse_area_report(
                self.__dc_area_report_files_[design_idx], self.__dc_design_names_[design_idx]
            )

    # Output the parse results to a summary file
    def write_report_summary(self, sum_file):
        # parse the report
        self.__parse_area_reports()
        # write to file
        os.makedirs(os.path.dirname(os.path.abspath(sum_file)), exist_ok=True)
        with open(sum_file, "w") as sumf:
            spamwriter = csv.writer(sumf, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            # Write head lines
            # Chomp ':'
            chomped_area_tags = []
            for curr_tag in AREA_TAGS:
                chomped_area_tags.append(curr_tag.rstrip(":"))
            spamwriter.writerow(["Design Name"] + chomped_area_tags)
            # Write data of designs one by one
            for design_name in self.__dc_design_names_:
                row_data = [design_name]
                for curr_tag in AREA_TAGS:
                    row_data.append(self.__rpt_db_[design_name][curr_tag])
                spamwriter.writerow(row_data)

    # Clear all the data
    def clear(self):
        self.__init__()
