lammps-tools
============

Разные полезности для удобной работы с LAMMPS

## Скрипты

### `archive_run.py`

Архиватор запусков LAMMPS. Запускает расчет, опционально компилирует дампы NEB, архивирует полезные файлы, удаляет ненужные файлы.

В начале скрипта словарь `patterns` хранит шаблоны имен файлов, которые будут заархивированы и удалены.

```
# python archive_run.py --help
usage: LAMMPS Runner [-h] [-c] [-d] [-n] [-m [MESSAGE ...]] [-r] command [command ...]

Runs LAMMPS, compiles NEB files, archives all data

positional arguments:
  command               LAMMPS command to run

options:
  -h, --help            show this help message and exit
  -c, --skip-neb        Skip compiling NEB
  -d, --skip-delete     Skip deletion of files
  -n, --skip-ntfy       Skip NTFY request
  -m [MESSAGE ...], --message [MESSAGE ...]
                        Create run description in description.txt. Skips doing it interactively
  -r, --recover         Try to recover a failed run, doing everything except running command
```

#### Пример запуска

`python archive_run.py -m "ontop K=100" -- mpirun -np 8 lmp -partition 8x1 -var K 100 -in ontop-neb.lmp`

`parallel -j1 tsp python archive_run.py -m "K={}" -- mpirun -np 8 lmp -partition 8x1 -var K {} -in ontop-neb.lmp ::: 1 10 100`

#### Зависимости

* `rich` (необязательно)
* `export LAMMPS_PYTHON_TOOLS=/<...>/lammps/tools/python/pizza` в файле `~/.bashrc` (см. [документацию](https://github.com/lammps/lammps/tree/develop/tools/python))

### `runs_analyze.py`

Анализатор расчетов LAMMPS, работающий с результатами расчетов, созданными скриптом выше. :warning:WIP:construction:

#### Зависимости

* `rich` (необязательно)
* `plotly`
* `pandas`

## Просмотрщики

* `view-lammpsdata-in-ase-3x3x1.cmd`
* `view-lammpsdata-in-ase.cmd`
* `view-poscar-in-ase-3x3x1.cmd`
* `view-poscar-in-ase.cmd`
* `view-xyz-in-ase-3x3x1.cmd`
* `view-xyz-in-ase.cmd`

При перетаскивании файла на этот скрипт откроется окно просмотрщика ASE. Скрипты с `3x3x1` в названии показывают ячейку, повторенную трижды вдоль осей X и Y.

* `lammpsdata` --- файлы, записанные LAMMPS директивой `write_data`
* `poscar` --- файлы POSCAR (VASP)
* `xyz` --- файлы [XYZ](https://en.wikipedia.org/wiki/XYZ_file_format)

Для работы необходим установленный [ASE](https://wiki.fysik.dtu.dk/ase/).

Аналогичный функционал предоставляет Ovito с модификатором Replicate.


## Прочее

### `run-with_lammps.cmd`

При перетаскивании файла на этот скрипт, файл будет запущен LAMMPS

### `add-ipynb-file-format.reg`

Добавляет в Windows возможность создать пустой ipynb из контекстного меню проводника
