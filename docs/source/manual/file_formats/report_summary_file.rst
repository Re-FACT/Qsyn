.. _file_format_report_summary_file:

Report Summary File (.csv)
==========================

The report summary file shows a dashboard about the post-synthesis area for all the blocks (subblocks are not included) in a given synthesis task.

.. csv-table:: Example report summary file
   :file: example_report_summary.csv
   :header-rows: 1

For all the supported synthesis tools, the following metrics are extracted from the reports.

- ``Design Name``: the unique name of the designs in synthesis tasks
- ``total_cell_area``: the total cell area of a block in the unit of standard cells. In most PDKs, the unit should be ``um`` but always double check with PDK vendors
- ``num_cells``: the total number of standard cells used in the block
