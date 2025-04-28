@echo off
python -c "import ase.io as io; from ase.visualize import view; data = io.read(open(r'%*','r'), index=0); view(data, repeat=(3,3,1))"
