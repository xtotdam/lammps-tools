#!/usr/bin/env python3

__author__ = 'xtotdam'
__version__ = '0.2'

patterns = dict(
    # these files will be copied to temp. folder
    runfiles = [
        '*.lmp', '*.ff', '*.molecule', '*.lammpsdata'
    ],
    # these files will be archived after run
    archive = [
        '*.lmp', '*.ff', '*.molecule',
        '*.lammpstrj', '*.lammpsdata', 
        'dump.neb.*', # 'dump.nonneb.*',
        'log.lammps', 'log.lammps.*', 'screen.*',
        'final.coords'
    ],
    # these afiles will be deleted after run
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
    print('Module "rich" not found, no pretty output for you')

from pathlib import Path
from shlex import join as shlex_join
import argparse
import datetime
import getpass
import io
import json
import os
import requests
import shutil
import subprocess
import tarfile
import time
import uuid
import zipfile


class LammpsRunner:
    def __init__(self, args):
        self.args = args
        self.run_id = hex(uuid.uuid1().time_low)[2:]

        self.command = shlex_join(args.command)
        self.message = ' '.join(args.message)

        self.cwd = Path.cwd()
        self.new_cwd = self.cwd / 'runs' / self.run_id

        self.metadata = dict()
        self.metadata['command'] = self.command
        self.metadata['description'] = self.message
        self.metadata['id'] = self.run_id

        timestring = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())
        # self.archive_name = f"lammpsrun_{timestring}_{self.metadata['id']}.tar.bz2"  # old
        self.archive_name = f"lammpsrun_{timestring}_{self.metadata['id']}.lmp.zip"

        self.starttime = time.time()


    def __str__(self):
        return f"<LammpsRunner [{self.run_id}] {self.message} === {self.command}>"

    ### check for common mistakes in script
    # uncommented quit?


    def copy_to_temp_dir(self):
        run_files = list()
        for p in patterns['runfiles']:
            run_files.extend(self.cwd.glob(p))

        print(run_files)

        self.new_cwd.mkdir(parents=True)
        for f in run_files: shutil.copy(f, self.new_cwd)


    def run_lammps(self):
        try:
            lammps_completed_process = subprocess.run(self.command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            e.add_note(f'Run ID = {self.run_id}')
            raise
        except KeyboardInterrupt:
            pass


    def compile_neb(self):
        try:
            for line in neb_compile_commands:
                cp = subprocess.run(line, shell=True)
                print(cp)
        except Exception as e:
            print('NEB compilation failed! Do it later manually')
            print(e)


    def create_file_lists(self):
        self.files_to_archive = list()
        self.files_to_delete = list()

        for p in patterns['archive']:
            new_files = list(self.new_cwd.glob(p))
            self.files_to_archive.extend(new_files)

        for p in patterns['delete']:
            new_files = list(self.new_cwd.glob(p))
            self.files_to_delete.extend(new_files)


    def archive_files_tarbz2(self):
        metadata_json = json.dumps(self.metadata, indent=2, sort_keys=True)
        metadata_info = tarfile.TarInfo('metadata.json')
        metadata_info.size = len(metadata_json)

        with tarfile.open(self.archive_name, 'w:bz2') as af:
            for f in self.files_to_archive:
                try:
                    af.add(f, arcname=f.name)
                except Exception as e:
                    print(e, f)

            af.addfile(metadata_info, io.BytesIO(metadata_json.encode()))

        return af.getmembers()


    def archive_files_zip(self):
        metadata_json = json.dumps(self.metadata, indent=2, sort_keys=True)

        with zipfile.ZipFile(self.archive_name, 'w', compresslevel=9, compression=zipfile.ZIP_LZMA) as af:
            for f in self.files_to_archive:
                try:
                    af.write(f, arcname=f.name)
                except Exception as e:
                    print(e, f)

            af.writestr('metadata.json', metadata_json)

        return af.infolist()


    def delete_files(self):
        for f in self.files_to_delete:
            print(f'Deleting {f}')
            f.unlink(missing_ok=True)


    def notify(self):
        ntfy_topic = os.getenv('NTFY_TOPIC')
        if ntfy_topic is None:
            print('Cannot notify: NTFY_TOPIC environment variable is not set. See ntfy docs for more info.')
            return None

        runtime = time.time() - self.starttime
        runtime = str(datetime.timedelta(seconds=runtime))

        cp = subprocess.run('tsp -l', shell=True, capture_output=True)
        out = cp.stdout.decode('utf8')
        running = out.count(' running ')
        queued = out.count(' queued ')

        title = f"[{self.run_id}] {self.message}"
        message = f'{self.command}\nRuntime {runtime} | @{self.cwd.stem}\n{running} run, {queued} in queue'

        if running + queued == 1: message += ' --- I am last!'

        print(message)

        try:
            requests.post(ntfy_topic, data=message.encode(encoding='utf-8'),
                headers={"Title": title})
        except Exception as e:
            print(e)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='LAMMPS Runner',
        description='Runs LAMMPS, compiles NEB files, archives all data', epilog=f'v{__version__}')
    parser.add_argument('-d', '--skip-delete',  action='store_true', help='Skip deletion of files')
    parser.add_argument('-n', '--skip-ntfy',    action='store_true', help='Skip NTFY request')
    parser.add_argument('-m', '--message', nargs='*', help='Run description')
    parser.add_argument('command', nargs='+', help='LAMMPS command to run')

    args = parser.parse_args()
    print(args)

    app = LammpsRunner(args)
    print(f'\n{app}\n')

    app.copy_to_temp_dir()

    os.chdir(app.new_cwd)
    app.run_lammps()
    app.compile_neb()
    os.chdir(app.cwd)

    app.create_file_lists()
    print('We archive:', app.files_to_archive)
    print('We delete:', app.files_to_delete)

    af = app.archive_files_zip()
    print(af)

    if not args.skip_delete:    app.delete_files()
    if not args.skip_ntfy:      app.notify()

    print(app.archive_name)
