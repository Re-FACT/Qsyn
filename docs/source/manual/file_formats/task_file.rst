.. _file_format_task_file:

Task File (.yaml)
=================

- The task file aims to provide a standard way for users to create a synthesis task run. 
- The task file is the key input file for users to craft, before running a synthesis task.
- The task file contains essential information required to set up synthesis scripts.

An example of file designed for synthesis tasks is shown as follows.

.. literalinclude:: example_qsyn_task.yaml
  :language: yaml


Technology-related Syntax
-------------------------

Technology-related information should be defined under the ``technology`` section

.. note:: The technology can be overwritten by the custom PDK file. See details in (:ref:`user_interface`). The corner selection will not be impacted 

.. option:: name="<string>"

  A unique name of the technology. Available technologies are ``s40ulp`` and ``t22ulp``

.. option:: root="<string>"

  Define the root directory of a PDK. Suggest to use absolute path when running a local test. 

.. option:: corner="<string>"

  Specify the corner to be considered for process variations. For example: 

  - ``tt``: typical-typical
  - ``tt_v1p0``: typical-typical, under Vdd=1.0V, only available for S40
  - ``tt_v1p1``: typical-typical, under Vdd=1.1V, only available for S40
  - ``tt85c``: typical-typical corner at the highest temperature required by commercial standard
  - ``bc``: best case
  - ``wc``: worst case

  .. note:: The corner names are defined in the PDK configuration (See details in :ref:`file_format_pdk_config_file`). The ``tag`` in PDK configuration represents the corner name here. If a corner is selected, only the standard cell libraries under the corresponding tag will be considered in optimization and technology mapping. 

Netlist-related Syntax
----------------------

Netlist-related information should be defined under the ``netlist`` section
The netlists are modeling the eFPGA fabric that are going to be analyzed

.. option:: input="<string>"

  Define the root directory of input (pre-synthesis) netlists where all the netlists (``.v`` or ``.v.gz``) are placed. Suggest to use absolute path when running a local test. 

.. option:: system_verilog_filter="<string>"

.. note:: This is optional

  By default, input files whose names end with ``sv`` will be recognized as system verilog netlists. Additional options will be appeneded to the auto-generated tcl scripts. This option provides an alternative for the input files which should be identified as system verilog netlists despite their file names. For example,

.. code-block:: yaml 

  netlist:
    input: "./release/"
    system_verilog_filter:
      - "pcounter_breg.v"
    exclude:
      - "counter_top.v"
    output: "./post_synth_netlist"

If you prefer all the netlists to be treated as system verilog, wildcard string is supported

.. code-block:: yaml 

  # All the verilog input netlists will be treated as system verilog
  netlist:
    input: "./release/"
    system_verilog_filter:
      - "*.v"
    exclude:
      - "counter_top.v"
    output: "./post_synth_netlist"

.. option:: exclude="<string>"

.. note:: This is optional

  Define the list of netlist files which should **NOT** be included when synthesis. For example, some netlists which are designed for simulation only, e.g., only include other netlists, are suggested to be excluded.

.. option:: link_path="<string>"

.. note:: This is optional when you are synthesizing RTL-level netlists

  Define the list of database files which are required to be linked before synthesis. For example, some IPs are treated as blackboxes during synthesis, which do require a timing library (.db) to be linked.

.. option:: output="<string>"

  Define the root directory of output (post-synthesis) netlists where all the netlists (``.v`` or ``.v.gz``) are placed. Suggest to use absolute path when running a local test. 

Synthesis Tasks
---------------

Report-area tasks should be defined under the ``report_area`` section.
Each task should constain the following information.

.. option:: name="<string>"

  Specify the unique name for this synthesis task. A synthesis task can be considered as a unique synthesis recipe, that are applicable to a number of designs (see definition in ``current_design``). The name and current design name will be used to create runtime directory.

.. option:: current_design="<string>"

  Specify the list of design names which the synthesis task should consider. All the designs under the same task will share the same synthesis receipe.

In the ``compile`` section, specify options when compile the design using synthesis tools 

.. option:: tool="<string>"

  Can be a valid tool name defined in the tool configuration file (See details in :ref:`file_format_tool_config_file`). Define the tool to be used when running synthesis. Currently support Synopsys Design Compiler and Yosys.

.. option:: optimization_recipe="<string>"

  Specify the path to a tcl/plain-text script where the detailed optimization recipe for the selected synthesis tool. This script will be embedded into the final tcl/plain-text script in the synthesis run. For example, if the Synopsys Design Compiler is considered, the script could be

.. code-block:: tcl

  compile_ultra -effort high

.. note:: When not specified, this is an analyze flow!

.. option:: target_library="<string>"

  Specify the target library(s) which optimization should utilize. The applicable library name depends on the technology node, which is defined in the PDK configuration (See details in :ref:`file_format_pdk_config_file`). Use the name of standard cell libary. For example, in the PDK configuration file, there are a number of standard cell libararies are defined.

.. code-block:: xml

  <sclibs>
    <sclib name="rvt">
      <!-- standard cell lib file definition -->
    </sclib>
    <sclib name="lvt">
      <!-- standard cell lib file definition -->
    </sclib>
    <sclib name="hvt">
      <!-- standard cell lib file definition -->
    </sclib>
  </sclibs>

.. code-block:: yaml

  # Use the standard cell libraries from PDK configuration
  target_library:
    - "lvt"
    - "hvt"

.. option:: sdc: 

  Specify a list of SDC files that the report timing task should consider
  Currently, we support files whose names end with ``.tcl`` or ``.sdc``.
  For example,

.. code-block:: yaml
  
  sdc:
    - sdc/user_case1.sdc
    - sdc/user_case2.sdc
    - sdc/user_case3.tcl

.. option:: save_session="<string>"

  When defined, the synthesis flow will be saved to a disk as a session. Easy for user to quickly reload and continue analysis. Session name can be customized through the string. For example,

.. code-block:: yaml

  save_session: my_session

.. option:: remove_time_stamp="<bool>"

  Specify if the time stamp in the synthesized netlists and report files will be removed or not. By default, it is removed.

.. option:: name_rule="<bool>"

  Specify if the simple name rule should be applied in the synthesized netlists. By default, it is applied. When enable, special characters will not be used in any names of nets and modules, to comply with Verilog syntax.

  .. note:: Only valid for Synopsys Design Compiler

In the ``reports`` section, define the report files (each task represents a file) to be outputted.

.. option:: name="<string>"

  Specify the unique name of the report task

.. option:: type="<string>"

  Specify if type of the report. Could be [ ``area_report`` | ``timing_report`` | ``power_report`` ]. When the ``area_report`` is selected, the reports will be parsed and a summary report will be outputted (See details in :ref:`file_format_report_summary_file`).

.. option:: path="<string>"

  Specify the path where the report file will be outputted.

  .. note:: Use the keyword ``[current_design]`` to generate report file path across different designs. Reserved words (see details in :ref:`file_format_task_file_reserved_words`) can be applied to value of each variable

.. option:: commands="<string>"

  List the commands to run in the selected synthesis tool when creating a report file. The commands will be executed serially.

  For example,

.. code-block::

  commands:
    - "hierachy -check"
    - "stat -liberty [current_target_lib] -json"

.. note:: You may use the keyword ``[current_target_lib]``, ``[current_path]`` and ``[current_design]``


.. option:: remove_time_stamp="<bool>"

  Remove the time stamp in the resulting report files.

Subblock Tasks
---------------
.. option:: subblock="<string>"

.. code-block:: yaml

  subblocks:
    - name: pi
      pattern: logical_tile_io_pi_mode_io_pi_
      flatten: false
      depends:
        - pi_ff
      compile:
        type: ultra
        optimize: area
        effort: high
      target_library_option: use
      target_library_subset: 
        - "*hvt*/*D1*"
        - "*lvt*/*D1*"
      sdc:
        - "./sdc/pi.tcl"

.. option:: name="<string>"

  Specify the unique name for this subblock task. A subblock task can be considered as a unique subblock recipe, that are applicable to a number of designs (:ref:`current_design`). The name and current design name will be used to create runtime directory.

.. option:: pattern="<string>"

  Specify the pattern to match the subblocks. It refers to the reference_name of this subblock.

.. code-block:: yaml
  
  subblocks:
    - name: pi
      pattern: logical_tile_io_pi_mode_io_pi_

.. option:: flatten="<bool>"

  Can be [True|False].The synthesis order of user-provided subblocks.

In the ``compile`` section, specify options when compile the design using synthesis tools 

.. option:: tool="<string>"

  Can be a valid tool name defined in the tool configuration file (See details in :ref:`file_format_tool_config_file`). Define the tool to be used when running synthesis. Currently support Synopsys Design Compiler and Yosys.

.. option:: optimization_recipe="<string>"

  Specify the path to a tcl/plain-text script where the detailed optimization recipe for the selected synthesis tool. This script will be embedded into the final tcl/plain-text script in the synthesis run. For example, if the Synopsys Design Compiler is considered, the script could be

.. code-block:: tcl

  compile_ultra -effort high

.. note:: When not specified, this is an analyze flow!


.. option:: target_library_option="<bool>"

    Can be [use|dont_use]. Specify whether to use the target library when optimization should utilize..The target_library_subset and target_library_option fields must be used in pairs — either define both together or omit both entirely.

   .. note:: Only valid for Synopsys Design Compiler

.. option:: target_library_subset="<list>"

    The target_library_subset and target_library_option fields must be used in pairs — either define both together or omit both entirely.

   .. note:: Only valid for Synopsys Design Compiler
  
  .. code-block:: yaml

    target_library_subset: 
      - "*hvt*/*D1*"
      - "*lvt*/*D1*"


.. option:: sdc: 

  This is optional.File suffix can be [".tcl", ".sdc"]

  Specify a list of SDC files that the report timing task should consider
  Currently, we support files whose names end with ``.tcl`` or ``.sdc``.
  For example,

.. code-block:: yaml
  
  sdc:
    - "./sdc/pi_ff.tcl"

.. option:: rename_prefix="<bool>"

    This is optional. Can be [ ``true`` | ``false`` ]. Specify whether to add a prefix to all the module and net names in the synthesized subblock netlist, to avoid name conflicts when integrating back to the top-level netlist. For example, ``subblock1_``.


.. _file_format_task_file_reserved_words:

Reserved words
``````````````

Name patterns can be used in the synthesis tasks. The following reserved word is supported

- ``[current_design]``: Once defined, the content will be replaced by the design name that is specified in the ``current_design`` syntax
- ``[current_path]``: Once defined, the content will be replaced by the final path that is specified in the ``path`` syntax of reports
- ``[current_target_lib]``: Once defined, the content will be replaced by the target library (there should be only 1 target library defined when used) that is specified in the ``target_library`` syntax
