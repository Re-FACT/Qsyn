.. _file_format_tool_config_file:

Tool Config File (.yaml)
========================

The tool config file contains a list of synthesis tools which can be used in a synthesis task (See details in :ref:`file_format_task_file`)

For each tool, detailed command-line options can be described for Qsyn to launch the tool

.. literalinclude:: example_tool_config.yaml
  :language: yaml

General Syntax
--------------

For each tool, a unique name should be defined. The name will be used as the tool name in the synthesis task file.

.. option:: bin="<string>"

  Specify the path to the binary executable of the synthesis tool. If the synthesis tool is in the system path, the detailed path can be omitted

.. option:: options="<string>"

  Specify the command-line options (detailed arguments) when calling the synthesis tool. There are two types of arguments supported:

  - ``kargs``: keyword arguments which can be swapped in command line options. For example, ``--config run,tcl``
  - ``pargs``: positional arguments which must appear in a fixed location of command-line options. For example, ``run.tcl``
  
  The ``options`` should define the sequence of the keyword arguments and positional arguments. For example, ``pargs kargs``. User can also define only keyword arguments or positioinal arguments is considered.


Positional Arguments
--------------------

Positional arguments should be defined under ``pargs``. A list of arguments can be defined in the syntax of ``name``.

.. option:: name="<string>"

  Specify a positional argument. For example, 

.. code-block::

  # The [tcl] will be replaced with an auto-generated tcl file
  # When calling yosys, the command line options will be 
  #   /usr/bin/yosys/yosys -s [tcl] 
  yosys:
    bin: /usr/bin/yosys/yosys
  options: "kargs"
  kargs:
    - name: "-s [tcl]"

Keyword Arguments
-----------------

Keyword arguments should be defined under ``kargs``. A list of arguments can be defined in the syntax of ``name``.

.. option:: name="<string>"

  Specify a positional argument. For example, 

.. code-block::

  # The [tcl] will be replaced with an auto-generated tcl file
  # When calling yosys, the command line options will be 
  #   /usr/bin/yosys/yosys [tcl] --log ys.log
  yosys:
    bin: /usr/bin/yosys/yosys
  options: "pargs kargs"
  pargs:
    - name: "[tcl]"
  kargs:
    - name: "--log ys.log"

