.. _file_format_pdk_config_file:

PDK Config File (.xml)
======================

The pdk config file contains detailed PDK-related information which can be used in a synthesis task (See details in :ref:`file_format_task_file`)

.. literalinclude:: example_pdk_config.yaml
  :language: yaml

General Syntax
--------------

.. option:: root="<string>"

  Specify the root path for the installed PDK. Will apply to each standard cell library file. The final root path will include the ``pdk_root`` defined in the synthesis task file

Standard Cell Library
---------------------

All the standard cell libraries should be defined under node ``sclibs``.

.. option:: name="<string>"

  Specify the unique name for the standard cell library, which synthesis tasks can specify as the reference and target libraries.

.. option:: tag="<string>"

  Specify the alias of the standard cell library file, representing the **Process, Voltage and Temperature** (PVT) corner. The PVT alias will be selected in synthesis tasks.
