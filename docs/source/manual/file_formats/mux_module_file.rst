.. _file_format_mux_module_file:

Mux Module File (.yaml)
=======================

The file describes the unique module names of routing multiplexers under each programmble blocks.
Once defined, under each selected programmable block, i.e., the design name defined in your task configuration file (see details in :ref:`file_format_task_file`), you can access module names in your custom SDC/Tcl file through variable ``${MUX_NAME_LIST}``

Here is an example of Custom tcl file:

.. code-block::

  # Apply different strategy for different muxes
  foreach MACRO_UNIT_NAME ${MUX_NAME_LIST} {
      set CURR_DESIGN_NAME [current_design]
	  current_design ${MACRO_UNIT_NAME} 
	  set_target_library_subset -dont_use "*/*LVT*"
	  set_max_fanout ${MAX_FANOUT} [current_design]
	  ungroup -all -flatten
	  link
	  compile_ultra
	  current_design ${CURR_DESIGN_NAME}
	  set_dont_touch [get_cells -hierarchical -filter "ref_name == ${MACRO_UNIT_NAME}"]
	  rename_design ${MACRO_UNIT_NAME} -prefix "${PREFIX}_" -update_links
  }

.. note:: These are module names, not instance names!

An example of file is shown as follows.

.. literalinclude:: example_mux_module.yaml
  :language: yaml
