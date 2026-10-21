# OpenEye Python Toolkits 2026.1.0 + PythonDS/v1.6

Образ PythonDS и штатные `pyds`/`pyds-exec` не изменяются. Новый модуль
загружает PythonDS/v1.6 и OpenEye/2026.1.0; пакеты доступны через
`openeye-pyds-exec`, а не через обычный `pyds-exec` или host Python.
Для интерактивной работы: `openeye-pyds-exec bash --norc`.

## 1. Проверка окружения на кластере

Перенести файлы комплекта на кластер (список в разделе 2). Выполнять от администратора установки,
имеющего доступ к образу, каталогу установки и лицензии. EasyBuild должен быть
доступен в текущем окружении; не использовать `module purge`, если он загружен модулем.

```bash
module load PythonDS/v1.6 OpenEye/2026.1.0
module list
command -v eb pyds-exec singularity
test -r "$PYTHONDS_CONTAINER"
test -r "$OE_LICENSE"
pyds-exec python -c 'import sys, platform; print(sys.executable); print(sys.version); print(platform.machine()); assert sys.version_info[:2] == (3,12); assert platform.machine() == "x86_64"'
pyds-exec python -m pip --version
pyds-exec getconf GNU_LIBC_VERSION
```

Образ, pip, Python 3.12 и архитектура должны быть подтверждены до установки.
Если в образе нет pip, остановиться и согласовать способ установки с владельцем
PythonDS; не устанавливать toolkit host Python вместо контейнерного.

## 2. Архив скриптов и отдельный wheel

В комплект уже включён архив
`sources/OpenEye-toolkits-2026.1.0-PythonDS-v1.6.tar.gz`.
Он содержит `payload/install.sh`, `payload/openeye-pyds-exec`,
`payload/verify.py`. Wheel в архив не входит. Добавить его отдельно на кластере
в каталог `sources/`, рядом с архивом, под точным именем:

```text
openeye_toolkits-2026.1.0-py312-none-manylinux_2_28_x86_64.whl
SHA256: 68b848356145c00735bb3a22682fa2f412b186efefddf98b72b158fa941c9db8
```

Метаданные: пакет `openeye-toolkits`, версия `2026.1.0`,
`Requires-Python: >=3.11,<3.15`, `Requires-Dist` не объявлены.
Тег wheel — `py312-none-manylinux_2_28_x86_64`: нужен Python 3.12,
Linux x86_64 и glibc не ниже 2.28 внутри контейнера.
Установщик использует `--no-index --no-deps`: сеть для pip не требуется.

Для установки перенести на кластер, сохраняя структуру:

```text
OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb
INSTALL.md
sources/
  OpenEye-toolkits-2026.1.0-PythonDS-v1.6.tar.gz
  SHA256SUMS
  openeye_toolkits-2026.1.0-py312-none-manylinux_2_28_x86_64.whl  # добавить на кластере
```

Исходный каталог `payload/` отдельно не требуется. Wheel обязателен.
После добавления wheel проверить оба исходных файла из директории комплекта:

```bash
(cd sources && sha256sum -c SHA256SUMS)
tar -tzf sources/OpenEye-toolkits-2026.1.0-PythonDS-v1.6.tar.gz
```

Checksums архива и отдельного wheel уже записаны в easyconfig. Запускать
`--inject-checksums` или переупаковывать архив на кластере не нужно.
`--enforce-checksums` при установке проверит оба checksum из easyconfig.
Если содержимое payload меняется, требуется новый архив и новый checksum;
не отключать проверку для изменённого архива.

## 3. Установка EasyBuild

Сначала проверить план; затем использовать принятые на сайте параметры
`--installpath`, `--buildpath`, module naming scheme и прочие настройки.
Пути сборки и установки должны быть доступны compute node и разрешены для bind.

```bash
eb OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb \
  --sourcepath="$PWD/sources" --dry-run
eb OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb \
  --sourcepath="$PWD/sources" --enforce-checksums
```

Не нужен `--robot`: оба модуля-зависимости должны уже существовать.
PythonDS объявлен внешним модулем. OpenEye ожидается как существующий модуль
SYSTEM из предоставленного easyconfig. При стандартной схеме именования
результат — `OpenEye-toolkits/2026.1.0-PythonDS-v1.6`.

Установка вычисляет SHA256 всего контейнера и сохраняет `container.sha256`:
это может занять время. Сохранить также `module show PythonDS/v1.6`, версии
runtime и штатных обёрток; один digest образа не фиксирует их поведение.

## 4. Проверки после установки

В новой сессии с обычным site окружением:

```bash
module load OpenEye-toolkits/2026.1.0-PythonDS-v1.6
module list
module show OpenEye-toolkits/2026.1.0-PythonDS-v1.6
command -v openeye-pyds-exec
openeye-pyds-exec python /opt/openeye-toolkits/share/openeye/verify.py
openeye-pyds-exec python /opt/openeye-toolkits/share/openeye/verify.py --license
openeye-pyds-exec python -m pip check
sha256sum -c "$OPENEYE_PYDS_ROOT/container.sha256"
openeye-pyds-exec python -c 'import numpy, pandas; from openeye import oechem; print(numpy.__version__, pandas.__version__, oechem.OEChemGetVersion())'
openeye-pyds-exec bash --norc
# В открывшейся оболочке:
python -c 'from openeye import oechem; print(oechem.OEChemGetVersion())'
exit
```

Дополнить проверку реальными библиотеками и операциями пользователя.
`pip check` проверяет всё видимое окружение: ошибки существующего PythonDS
нужно отделить от новых, сравнив с `pyds-exec python -m pip check`.
Проверка `--license` покрывает OEChem, но не подтверждает лицензии всех toolkit
и работу GPU. Для OEOmega/OEDocking и других используемых API нужны отдельные
минимальные операции. Повторить те же проверки в job на целевой compute node
с принятым на сайте scheduler header и инициализацией modules.

После выхода из интерактивной оболочки:

```bash
module unload OpenEye-toolkits/2026.1.0-PythonDS-v1.6
if command -v openeye-pyds-exec; then
  echo 'ERROR: wrapper still on PATH; check another loaded module/installation'
fi
```

Обёртка экспортирует переменные только в своём дочернем процессе, поэтому
обычный `pyds-exec` не получает toolkit ни до, ни после её запуска.
Внутри контейнера подключаются read-only только каталог установки и каталог
лицензии; приложения OpenEye с хоста автоматически внутрь не подключаются.
`OE_LICENSE` должен быть путём к читаемому файлу, а не строкой сервера лицензий.

## Локальная проверка комплекта

```bash
bash -n payload/openeye-pyds-exec payload/install.sh
shellcheck payload/openeye-pyds-exec payload/install.sh
python3 -m unittest discover -s tests -v
```

Это проверка обёртки с подставным `pyds-exec`, не запуск реального контейнера.
EasyBuild, wheel, лицензия и приложения на кластере требуют выполнения шагов выше.

Источники: [EasyBuild external modules](https://docs.easybuild.io/using-external-modules/),
[Binary easyblock](https://docs.easybuild.io/version-specific/generic-easyblocks/),
[OpenEye installation](https://docs.eyesopen.com/toolkits/python/quickstart-python/install.html),
[Apptainer environment](https://apptainer.org/docs/user/latest/environment_and_metadata.html).
