#!/usr/bin/env python3

__author__ = 'xtotdam'
__version__ = '0.1'

patterns = dict(
    archive = [
        '*.lmp', '*.ff', '*.molecule',
        '*.lammpstrj', '*.lammpsdata', 
        'dump.neb.*',
        # 'dump.nonneb.*',
        'log.lammps', 'log.lammps.*', 'screen.*',
        'final.coords'
    ],
    delete = [
        'dump.neb.*', 'dump.nonneb.*', 'out.*.lammpsdata', 'out.replica.*.lammpstrj',
        'log.lammps', 'log.lammps.*', 'screen.*',
        'tmp.lammps.variable'
    ]
)

neb_compile_commands = [
    'python /home/syromyatnikov/lammps/tools/python/neb_final.py   -o neb-dump.final.lammpsdata   -b dump.nonneb.1 -r dump.neb.*',
    'python /home/syromyatnikov/lammps/tools/python/neb_combine.py -o neb-dump.combine.lammpsdata -b dump.nonneb.1 -r dump.neb.*'
]

try:
    from rich import print
except ImportError:
    print('Module "rich" not found, no problem')

import argparse
parser = argparse.ArgumentParser(prog='LAMMPS Runner', description='Runs LAMMPS, compiles NEB files, archives all data', epilog=f'v{__version__}')
parser.add_argument('-c', '--skip-neb', action='store_true', help='Skip compiling NEB')
parser.add_argument('-d', '--skip-delete', action='store_true', help='Skip deletion of files')
parser.add_argument('-n', '--skip-ntfy', action='store_true', help='Skip NTFY request')
parser.add_argument('-m', '--message', nargs='*', help='Create run description in description.txt. Skips doing it interactively')
parser.add_argument('-r', '--skip-run', action='store_true', help='Try to recover a failed run, doing everything except running LAMMPS directly')
parser.add_argument('command', nargs='+', help='LAMMPS command to run')
args = parser.parse_args()
args.message = ' '.join(args.message)
print(args)



### check for common mistakes in script
# uncommented quit?



### run LAMMPS
if not args.skip_run:
    import subprocess
    print('Command:', args.command)
    cp = subprocess.run(args.command, shell=True)
    print(cp)

    if cp.returncode != 0:
        print(f'Return code != 0, but {cp.returncode}')
        exit(cp.returncode)



### time string -> archive name
import time
timestring = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
import uuid
u = uuid.uuid1().time_low
archive_name = f'lammpsrun_{timestring}_{u:x}.tar.bz2'
print('Archive name:', archive_name)



### compiling NEB
if not args.skip_neb:
    for line in neb_compile_commands:
        cp = subprocess.run(line, shell=True)
        print(cp)



### collecting metadata
metadata = dict()
metadata['command'] = args.command
metadata['description'] = args.message
metadata['id'] = f'{u:x}'

import json
metadata_json = json.dumps(metadata, indent=2, sort_keys=True)


### get list of all files
from pathlib import Path
cwd = Path.cwd()
files_to_archive, files_to_delete = list(), list()

for p in patterns['archive']:
    new_files = list(cwd.glob(p))
    files_to_archive.extend(new_files)

for p in patterns['delete']:
    new_files = list(cwd.glob(p))
    files_to_delete.extend(new_files)

# files_to_archive = [x.relative_to(cwd) for x in files_to_archive]
# files_to_delete = [x.relative_to(cwd) for x in files_to_delete]
print('We archive:', files_to_archive)
print('We delete:', files_to_delete)



### create archive
import tarfile
import io

metadata_info = tarfile.TarInfo('metadata.json')
metadata_info.size = len(metadata_json)

with tarfile.open(archive_name, 'w:bz2') as af:
    for f in files_to_archive:
        try:
            af.add(f, arcname=f.name)
        except Exception as e:
            print(e, f)

    af.addfile(metadata_info, io.BytesIO(metadata_json.encode()))

    print(af.getmembers())



### delete files
if not args.skip_delete:
    print('Deleting:')
    for f in files_to_delete:
        print(f)
        f.unlink(missing_ok=True)



### send notification
if not args.skip_ntfy:
    import getpass
    import requests

    topic = getpass.getuser()
    message = f'{args.message}\n{args.command}\n{archive_name}'
    requests.post(f"https://***REMOVED***/{topic}", data=message.encode(encoding='utf-8'))


# in the end
print(archive_name)
