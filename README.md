# OpenEye Toolkits easyconfigs

EasyBuild recipes and supporting scripts for OpenEye. The current PythonDS
integration provides **OpenEye Python Toolkits 2026.1.0 inside PythonDS/v1.6**
without modifying the PythonDS container image or its standard launch scripts.

## Recipes

| Easyconfig | Purpose |
| --- | --- |
| `OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb` | Python toolkits installed externally and used through PythonDS/v1.6 |
| `OpenEye-2026.1.0.eb` | Host command-line applications and C++ toolkits; a dependency of the Python toolkit module |
| `OpenEye-toolkits-2025.2.3-GCCcore-12.3.0.eb` | Earlier Python toolkit recipe using a conventional Python/GCCcore environment |

The instructions below apply to the **2026.1.0-PythonDS-v1.6** recipe.

## Build requirements

- EasyBuild configured for the site's module system and installation paths.
- Existing modules `PythonDS/v1.6` and `OpenEye/2026.1.0`.
- The site's `pyds-exec` launcher and Singularity/Apptainer runtime.
- Python **3.12**, pip, Linux x86_64 and glibc **2.28 or newer** inside PythonDS.
- Read access to the PythonDS container image and the OpenEye license file.
- Writable build and installation directories, with container bind mounts permitted.

PythonDS is declared as an external module dependency. The OpenEye applications
module uses the SYSTEM toolchain. Do not add a host Python dependency: installation
must use the Python interpreter inside PythonDS.

Keep EasyBuild available when loading dependencies. The supplied PythonDS module
unloads some host Python-related modules, so check that `eb` remains usable.

## Prepare the sources

Place the following files on the build host:

```text
OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb
sources/
├── OpenEye-toolkits-2026.1.0-PythonDS-v1.6.tar.gz
├── SHA256SUMS
└── openeye_toolkits-2026.1.0-py312-none-manylinux_2_28_x86_64.whl
```

**Supply the wheel separately on the cluster. Do not add it to the tar archive.**
The archive contains only:

```text
payload/install.sh
payload/openeye-pyds-exec
payload/verify.py
```

Obtain the exact wheel from the approved OpenEye distribution source. Its SHA256 is:

```text
68b848356145c00735bb3a22682fa2f412b186efefddf98b72b158fa941c9db8
```

Both source checksums are pinned in the easyconfig. From the directory containing
the easyconfig, verify the files:

```bash
(cd sources && sha256sum -c SHA256SUMS)
tar -tzf sources/OpenEye-toolkits-2026.1.0-PythonDS-v1.6.tar.gz
```

If the archive is absent from a checkout, copy the matching prepared archive into
`sources/`. If rebuilding it from `payload/`, update its checksum in both the
easyconfig and `sources/SHA256SUMS`; repacking can change the archive checksum
even when the scripts are unchanged. Keep the wheel checksum unchanged unless
the approved wheel itself changes.

## Build and install

Load and inspect the dependencies:

```bash
module load PythonDS/v1.6 OpenEye/2026.1.0
module list
command -v eb pyds-exec singularity
printf 'PythonDS version: %s\n' "${PYTHONDS_VERSION:-UNSET}"
test -r "$PYTHONDS_CONTAINER"
test -r "$OE_LICENSE"
pyds-exec python -c 'import sys, platform; print(sys.version); print(platform.machine()); assert sys.version_info[:2] == (3, 12); assert platform.machine() == "x86_64"'
pyds-exec python -m pip --version
pyds-exec getconf GNU_LIBC_VERSION
```

Confirm `PYTHONDS_VERSION=v1.6`, Python 3.12 and glibc >= 2.28. If pip is missing,
resolve this with the PythonDS maintainer before building.

Check the plan, then install using the site's normal EasyBuild configuration:

```bash
eb OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb \
  --sourcepath="$PWD/sources" --dry-run

eb OpenEye-toolkits-2026.1.0-PythonDS-v1.6.eb \
  --sourcepath="$PWD/sources" --enforce-checksums
```

Add site-specific build/install path options as needed. Both dependency modules
must already exist; `--robot` is not required for this procedure.

The installer uses container Python with `pip --isolated install --no-index
--no-deps --no-compile --target ...`. It writes packages to the external
installation directory, copies the launcher and verification script, and records
the container image checksum in `container.sha256`. Hashing a large image can
take some time. The wheel declares no additional Python package dependencies.

With the standard module naming scheme, the resulting module is:

```text
OpenEye-toolkits/2026.1.0-PythonDS-v1.6
```

## Validate the installation

In a fresh user session, add the installation's module directory if it is not
already on `MODULEPATH`, then load the module:

```bash
# Example for the scratch installation; replace for your deployment:
module use /scratch/shtanan1/easybuild/modules/all
module load OpenEye-toolkits/2026.1.0-PythonDS-v1.6
module list
command -v openeye-pyds-exec

# Check Python, toolkit package version and import location:
openeye-pyds-exec python /opt/openeye-toolkits/share/openeye/verify.py

# Also check the OEChem license and a small molecule operation:
openeye-pyds-exec python /opt/openeye-toolkits/share/openeye/verify.py --license
```

The license check should end with:

```text
OEChem license and molecule operation: PASS
```

Check integration with PythonDS libraries:

```bash
openeye-pyds-exec python - <<'PY'
import numpy
import pandas
from openeye import oechem

mol = oechem.OEGraphMol()
assert oechem.OESmilesToMol(mol, "CCO")
assert mol.NumAtoms() == 3
print("NumPy:", numpy.__version__)
print("pandas:", pandas.__version__)
print("OEChem:", oechem.OEChemGetVersion())
print("PASS")
PY
```

OEChem's component version can differ from the toolkit distribution version.
The OEChem test does not establish licensing or functionality for every toolkit
or GPU feature. Test the APIs actually used by the user and repeat the workload
on the target compute node through the site's scheduler.

Optional diagnostics:

```bash
openeye-pyds-exec python -m pip check
pyds-exec python -m pip check
sha256sum -c "$OPENEYE_PYDS_ROOT/container.sha256"
```

Compare both `pip check` outputs to distinguish pre-existing PythonDS issues.
The container checksum is recorded at installation time; it is not automatically
checked on every launch. Keep the PythonDS module and launcher versions with
the build records as well.

## User guide

### Load the module

```bash
# Only needed if this directory is not already in the module search path:
module use /scratch/shtanan1/easybuild/modules/all
module load OpenEye-toolkits/2026.1.0-PythonDS-v1.6
```

The scratch path above is an example deployment path. Use the module directory
provided by your administrator. PythonDS/v1.6 and OpenEye/2026.1.0 load automatically.

### Run a Python script

```bash
openeye-pyds-exec python my_script.py
openeye-pyds-exec python my_script.py input.sdf output.sdf
```

The script and data must be accessible inside the container. Use directories
exposed by the site's PythonDS launcher; an arbitrary host directory may require
an additional site-approved bind mount.

### Work interactively

Start Python directly:

```bash
openeye-pyds-exec python
```

```python
from openeye import oechem

mol = oechem.OEGraphMol()
oechem.OESmilesToMol(mol, "CCO")
print(mol.NumAtoms())
```

Use `exit()` or Ctrl+D to leave Python. To start a container shell with OpenEye:

```bash
openeye-pyds-exec bash --norc
```

Inside that shell, run `python` or `python my_script.py`. Use `exit` to leave.
Load environment modules on the host before entering the container; `ml` is not
expected to be available inside it.

For batch jobs, initialize the site's module system and use the same module load
and `openeye-pyds-exec python ...` commands in the job script, with the appropriate
scheduler resource settings.

Unload the toolkit module on the host when finished:

```bash
module unload OpenEye-toolkits/2026.1.0-PythonDS-v1.6
```

## How the launcher works

`openeye-pyds-exec` calls the existing `pyds-exec`, retaining its container startup
and `--app plenty` setup. For that child process it sets the container Python
search path and license environment, and adds read-only mounts:

| Host location | Container location |
| --- | --- |
| Toolkit installation directory | `/opt/openeye-toolkits` |
| Directory containing the license file | `/opt/openeye-license` |

`/opt/openeye-toolkits/share/openeye/verify.py` is therefore a **container path**,
not the host installation path. The wrapper expects `OE_LICENSE` to identify a
readable host file, with a site-specific fallback defined in the script.

Use **`openeye-pyds-exec`** to access the Python toolkit. Standard `pyds`,
`pyds-exec`, and host `python` do not automatically receive this configuration.
Host OpenEye application binaries are not mounted by this wrapper.

## Troubleshooting

- **`load PythonDS/v1.6 first`:** the wrapper requires
  `PYTHONDS_VERSION=v1.6`. Inspect `module list`, `PYTHONDS_VERSION`,
  `PYTHONDS_CONTAINER`, and `command -v pyds-exec`. If this happens during
  EasyBuild sanity checking, inspect dependency loading in the build log;
  loading the module in the parent shell does not prove those variables reached
  the sanity-check process. Changing the `/opt` path does not fix this error.
- **License file is not readable:** check `OE_LICENSE` and permissions on the
  host. Even the import-only sanity command requires a readable license file
  because the wrapper mounts its directory. `--license` additionally checks
  that OEChem accepts the license.
- **Checksum failure:** verify that both sources have the exact expected names
  and contents. Do not disable checksum enforcement.
- **Import or shared-library error:** confirm the container Python version,
  architecture, system libraries and bind mounts; reproduce using the wrapper.
- **Missing user script or input:** check visibility of the working/data directory
  inside PythonDS, not just on the host.

## Maintaining the integration

Changes to `payload/` must also be included in the script archive. Update the
archive checksum in the corresponding easyconfig and `sources/SHA256SUMS`.
For a different wheel, PythonDS image or Python version, review the compatibility
checks and create an appropriately versioned recipe rather than silently
replacing the pinned inputs. Keep large wheels outside normal Git history.

Local checks for script changes:

```bash
bash -n payload/openeye-pyds-exec payload/install.sh
shellcheck payload/openeye-pyds-exec payload/install.sh
python3 -m unittest discover -s tests -v
```

These checks use a stub launcher and do not replace validation with the real
container, license and user workload on the cluster.
