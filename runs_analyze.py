#!/usr/bin/env python3

__author__ = 'xtotdam'
__version__ = '0.2'

from pathlib import Path
import tarfile
import zipfile
import json
from io import StringIO
from functools import cache

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

try:
    from rich import print
except ImportError:
    print('Module "rich" not found, no problem')

from typing import Union, List, Dict, Tuple


class LammpsRunFolder:
    def __init__(self, path:Union[str,Path]):
        if isinstance(path, str):
            path = Path(path)
        self.path = path.absolute()


    def __repr__(self):
        return f'<LammpsRunFolder {self.path} : {len(self.find())} runs>'


    def find(self, pattern:str='*'):
        ''' can be used like find('*id*') '''
        runs1 = self.path.glob(f'lammpsrun_{pattern}.tar.bz2')
        runs2 = self.path.glob(f'lammpsrun_{pattern}.lmp.zip')
        return sorted(list(runs1) + list(runs2))


    def get_by_id(self, _id:str):
        _id = _id.strip()
        if not _id: return None
        pattern = f'*{_id}*'
        runs = self.find(pattern)
        if len(runs) == 1:
            return runs[0]
        else:
            print('Multiple runs with this id:', _id)
            return None


    def describe(self, verbose=False):
        '''print info about folder'''
        runs = self.find()
        print(f'{self.path} --- {len(runs)} runs')
        if verbose:
            description = '\n'.join(str(LammpsRun(run)) for run in runs)
            description = description.replace('\t[None]', '')
            print(description)




class LammpsRun:
    def __init__(self, archive:Union[str,Path]):
        if not isinstance(archive, Path):
            archive = Path(archive)
        self.path = archive
        self.filename = str(self.path.name)
        self.neb_df = None

        if self.path.name.endswith('.tar.bz2'):
            with tarfile.open(self.path, 'r') as archive:

                try:
                    self.metadata = json.load(archive.extractfile('metadata.json'))
                except KeyError:
                    self.metadata = dict()

                    # legacy
                    try:
                        self.metadata['command'] = archive.extractfile('command.sh').read().decode('utf8')
                    except KeyError:
                        self.metadata['command'] = None

                    try:
                        self.metadata['description'] = archive.extractfile('description.txt').read().decode('utf8')
                    except KeyError:
                        self.metadata['description'] = None

                    self.metadata['id'] = self.path.name.split('.')[0].split('_')[-1]

        if self.path.name.endswith('.lmp.zip'):
            with zipfile.ZipFile(self.path, 'r') as archive:
                self.metadata = json.load(archive.open('metadata.json'))
        
        self.description = self.metadata['description']
        self.command     = self.metadata['command']
        self.id          = self.metadata['id']


    def __repr__(self):
        return f'<LammpsRun {self.path}>'


    def __str__(self):
        return f'* <{self.metadata["id"]}> {self.path.name}\t[{self.metadata["description"]}]\n    CMD: {self.metadata["command"]}'


    def get_file(self, name:str):
        if self.path.name.endswith('.tar.bz2'):
            with tarfile.open(self.path, 'r') as archive:
                return StringIO(archive.extractfile(name).read().decode())

        if self.path.name.endswith('.lmp.zip'):
            with zipfile.ZipFile(self.path, 'r') as archive:
                return StringIO(archive.open(name).read().decode())


    def update_metadata(self, new_metadata:dict):
        print('update_metadata not implemented')


    @cache
    def parse_neb(self, quiet:bool=True):
        if self.neb_df is not None:
            print(f'<{self.id}> Neb dataframe already created')
            return

        lines = self.get_file('log.lammps').readlines()

        N = int(lines[1].split(' ')[2])
        self.neb_replicas = N

        # finding climbing part of neb run
        climbing_line = None
        for i,line in enumerate(lines):
            if 'Climbing' in line:
                climbing_line = i
                break

        # df1 = pd.read_csv(StringIO(''.join(lines[2:climbing_line])), sep=r'\s+')   # initial NEB
        df2 = pd.read_csv(StringIO(''.join(lines[climbing_line+1:])), sep=r'\s+')    # climbing NEB
        self.neb_df = df2

        if not quiet:
            print(f'<{self.id}> Neb parse success: {N} replicas, {len(df2)} lines of data')


    def view_lammpsdata_with_ase(self, _file:str, repeat:Tuple[int,int,int]=(1,1,1), units:str='real', atom_style:str='charge'):
        import ase.io.lammpsdata as lammpsdata
        from ase.visualize import view

        data = lammpsdata.read_lammps_data(self.get_file(_file), units=units, atom_style=atom_style)
        view(data, repeat=repeat)


    def get_3d_energy_traj_traces(self):
        data = list()
        for i in range(self.neb_replicas):
            data.extend(px.line_3d(self.neb_df, x='Step', y=f'RD{i+1}', z=f'PE{i+1}').data)
        return data


    def get_energy_path_traces(self, row:int=-1, substract_min:bool=True, name:str=None, quiet:bool=True, show_energies=True, factor=1.):
        rd = self.neb_df.iloc[row].get([f'RD{x}' for x in range(1, self.neb_replicas+1)]).values
        pe = self.neb_df.iloc[row].get([f'PE{x}' for x in range(1, self.neb_replicas+1)]).values

        if not quiet:
            print(f'<{self.id}> Energy bottom: {pe.min()}')

        if substract_min:
            pe = pe - pe.min()

        en = ''
        if show_energies:
            le = (pe.max() - pe[0])*factor
            he = (pe.max() - pe[-1])*factor
            en = f' [{le:.3f} / {he:.3f}]'

        if name is None:
            name = f'{self.id} row {row}{en}'
        else:
            if name.startswith('+'):
                name = f'{self.id} row {row} {name[1:]}{en}'

        trace = go.Scatter(x=rd, y=factor*pe, mode='lines+markers', name=name)
        return trace


    def get_transition_evolution_traces(self, factor=1.):
        df = self.neb_df.copy()
        traces = list()

        start_trace = self.get_energy_path_traces(row=0, substract_min=False, factor=factor)
        start_trace.line = dict(color='#ee0000', width=2)
        start_trace.marker = dict(size=15)

        finish_trace = self.get_energy_path_traces(row=-1, substract_min=False, factor=factor)
        finish_trace.line = dict(color='#00aa00', width=2)
        finish_trace.marker = dict(size=15)

        traces = [start_trace, finish_trace]

        for i in range(1, self.neb_replicas+1):
            df[f'PE{i}'] *= factor
            traces.extend(px.scatter(df, x=f"RD{i}", y=df[f"PE{i}"], color="Step", height=400).data)

        return traces




if __name__ == '__main__':
    lrf = LammpsRunFolder('.')
    # lrf.describe()

    run = LammpsRun(lrf.find('*53ab196*')[0])
    print(run)

    run.parse_neb()


    fig = go.Figure()
    # fig.add_traces(run.get_3d_energy_traj_traces())
    fig.add_traces(run.get_energy_path_traces())
    fig.show()

    # run.draw_energy_path()

    # run.view_lammpsdata_with_ase('out.1.lammpsdata')

