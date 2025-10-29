lammps-tools
============

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/xtotdam/lammps-tools/blob/master/README.en.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17471957.svg)](https://doi.org/10.5281/zenodo.17471957)



Разные полезности для удобной работы с LAMMPS

## Скрипты

### `archive_run.py`

Архиватор запусков LAMMPS. Копирует файлы во временную папку, запускает расчет, опционально компилирует дампы NEB, архивирует полезные файлы, удаляет ненужные файлы.
Позволяет запускать несколько расчетов на одинаковых файлах с разными параметрами одновременно параллельно.

В начале скрипта словарь `patterns` хранит шаблоны имен файлов, которые будут заархивированы и удалены.

```
# python archive_run.py --help
usage: LAMMPS Runner [-h] [-d] [-n] [-m [MESSAGE ...]] command [command ...]

Runs LAMMPS, compiles NEB files, archives all data

positional arguments:
  command               LAMMPS command to run

options:
  -h, --help            show this help message and exit
  -d, --skip-delete     Skip deletion of files
  -n, --skip-ntfy       Skip NTFY request
  -m [MESSAGE ...], --message [MESSAGE ...]
                        Run description

v0.2
```

#### Пример запуска

`python archive_run.py -m "ontop K=100" -- mpirun -np 8 lmp -partition 8x1 -var K 100 -in ontop-neb.lmp`

Предполагая, что положение скрипта находится в `$PATH`, полноценный запуск с постановкой в очередь задач и подстановкой параметров:

`parallel -j1 tsp archive_run.py -m "K={}" -- mpirun -np 8 lmp -partition 8x1 -var K {} -in ontop-neb.lmp ::: 1 10 100`

#### Зависимости

* `rich` (необязательно)
* `export LAMMPS_PYTHON_TOOLS=/<...>/lammps/tools/python/pizza` в файле `~/.bashrc` (см. [документацию](https://github.com/lammps/lammps/tree/develop/tools/python))

### `runs_analyze.py`

Анализатор расчетов LAMMPS, работающий с результатами расчетов, созданными скриптом выше. :warning:WIP:construction:

TODO: Docs!!

#### Зависимости

* `rich` (необязательно)
* `plotly`
* `pandas`

#### Пример использования

```py
from tqdm.notebook import tqdm
import plotly.graph_objects as go
import runs_analyze as ra
LammpsRunFolder, LammpsRun = ra.LammpsRunFolder, ra.LammpsRun

lrf = LammpsRunFolder('runs/p-2mol1')
lrf.describe() # кратко выведет найденные файлы

runs = [ra.LammpsRun(run) for run in lrf.find()]

for run in tqdm(runs):
    run.parse_neb()

# профиль потенциального барьера
fig = go.Figure(layout=dict(width=1000, height=700, xaxis_title_text='Reaction coordinate', yaxis_title_text='Energy, kcal/mol'))
for run in runs:
    fig.add_traces(run.get_energy_path_traces(name=f'+{run.metadata["description"]}'))
fig.show()

# просмотреть требуемый файл с помощью ASE
runs[2].view_lammpsdata_with_ase('out.2.lammpsdata')

# его изменение в течение расчета
for run in runs:
    fig = go.Figure(layout=dict(width=1000, height=700, title=run.metadata['description']))
    fig.add_traces(run.get_transition_evolution_traces())
    fig.show()

# то же в 3D
for run in runs:
    fig = go.Figure(layout=dict(width=1000, height=700, title=run.metadata['description']))
    fig.add_traces(run.get_3d_energy_traj_traces())
    fig.show()
```

## Просмотрщики

* `view-lammpsdata-in-ase[-3x3x1].cmd` --- для файлов, записанных LAMMPS директивой `write_data`
* `view-poscar-in-ase[-3x3x1].cmd` --- для файлов POSCAR (VASP)
* `view-xyz-in-ase[-3x3x1].cmd` --- для файлов [XYZ](https://en.wikipedia.org/wiki/XYZ_file_format)

При перетаскивании файла на этот скрипт откроется окно просмотрщика ASE. Скрипты с `3x3x1` в названии показывают ячейку, повторенную трижды вдоль осей X и Y.

Для работы необходим установленный [ASE](https://wiki.fysik.dtu.dk/ase/).

Аналогичный функционал предоставляет Ovito с модификатором Replicate.


## Прочее

### `run-with_lammps.cmd`

При перетаскивании файла на этот скрипт, файл будет запущен LAMMPS

### `add-ipynb-file-format.reg`

Добавляет в Windows возможность создать пустой ipynb из контекстного меню проводника
