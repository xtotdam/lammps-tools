#!/bin/bash

python ~/lammps/tools/python/neb_final.py   -o neb-dump.final.lammpsdata   -b dump.nonneb.1 -r dump.neb.*
python ~/lammps/tools/python/neb_combine.py -o neb-dump.combine.lammpsdata -b dump.nonneb.1 -r dump.neb.*
