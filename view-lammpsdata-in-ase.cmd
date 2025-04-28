@echo off
python -c "import ase.io.lammpsdata as lammpsdata; from ase.visualize import view; data = lammpsdata.read_lammps_data(r'%*'); view(data)"
