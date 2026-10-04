# Skywater 130nm open-source PDK

All the tests are based a prebuilt version of the PDK.
Only standard cells are required to run synthesis tasks.

You may download the package for standard cells from

```
wget https://github.com/Re-FACT/Qsyn/releases/download/v0.0.0/sky130_std_cells.tar.gz
tar -xzvf sky130_std_cells.tar.gz
```

Note that this package is extracted from a prebuilt version (2026.08.27) of the PDK 
To access the complete PDk, use the following to install: 

```
# Install ciel to install OpenPDK
python3 -m pip install ciel
ciel ls-remote --pdk-family sky130
# The follow command is designed for bash. Adapt if you are in a different shell
export PDK_ROOT=${PWD}
# The PDK will be installed in the current directory. Standard cells can be found under sky130A/libs.ref 
ciel enable --pdk-family sky130 1689ac3f2dc763876eaf967227c7dfe831b031ae
```
