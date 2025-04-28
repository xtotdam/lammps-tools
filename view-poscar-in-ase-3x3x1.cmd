@echo off
rem python -c "import ase.io.xyz as xyz; from ase.visualize import view; data = xyz.read_xyz(open(r'%*','r'), index=0); view(data)"
python -c "import ase.io.vasp as vasp; from ase.visualize import view; data = vasp.read_vasp(open(r'%*','r')); view(data, repeat=(3,3,1))"
