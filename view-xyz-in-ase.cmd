@echo off
rem python -c "import ase.io.xyz as xyz; from ase.visualize import view; data = xyz.read_xyz(open(r'%*','r'), index=0); view(data)"
python -c "import ase.io as io; from ase.visualize import view; data = io.read(open(r'%*','r'), index=0); view(data)"
