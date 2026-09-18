.. _file_format_config_mem_file:

Config Mem File (.yaml)
=======================

The file describes the instance name of configuration memory module under each programmble blocks.
Once defined, under each selected programmable block, i.e., the design name defined in your task configuration file (see details in :ref:`file_format_task_file`), you can access module names in your custom SDC/Tcl file through variable ``${CONFIG_GROUP_MEM}``

.. note:: These are instance names, not module names!

Here is an example of Custom tcl file:

.. code-block::

  # Apply different strategy for different configuration memory
  set MACRO_UNIT_NAME ${CONFIG_GROUP_MEM}
  set CURR_DESIGN_NAME [current_design]
  current_design ${MACRO_UNIT_NAME}
  set_target_library_subset -dont_use "*/*LVT*"
  link
  compile_ultra
  source ${MACRO_UNIT_NAME}_tcl_buf_prog_clk.tcl
  source ${MACRO_UNIT_NAME}_tcl_buf_prog_reset.tcl
  source ${MACRO_UNIT_NAME}_tcl_del.tcl
  current_design ${CURR_DESIGN_NAME}
  set_dont_touch [get_cells ${MACRO_UNIT_NAME}]

An example of file is shown as follows.

.. literalinclude:: example_config_mem.yaml
  :language: yaml
