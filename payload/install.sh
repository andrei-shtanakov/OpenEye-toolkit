#!/usr/bin/env bash
set -euo pipefail
src=$(cd -- "$1" && pwd -P)
mkdir -p -- "$2"
dest=$(cd -- "$2" && pwd -P)
wheel_dir=$(cd -- "$3" && pwd -P)
[[ ${PYTHONDS_VERSION:-} == v1.6 ]] || { echo 'PythonDS/v1.6 required' >&2; exit 2; }
: "${PYTHONDS_CONTAINER:?PythonDS container required}"
for path in "$src" "$dest" "$wheel_dir"; do
    [[ $path != *:* && $path != *,* ]] || { echo 'Invalid bind path' >&2; exit 2; }
done
shopt -s nullglob
wheels=("$wheel_dir"/*.whl)
[[ ${#wheels[@]} == 1 ]] || { echo 'Exactly one OpenEye wheel required' >&2; exit 2; }
bindings="$wheel_dir:/opt/openeye-source:ro,$dest:/opt/openeye-install:rw"
export SINGULARITY_BINDPATH="${SINGULARITY_BINDPATH:+$SINGULARITY_BINDPATH,}$bindings"
export APPTAINER_BINDPATH="${APPTAINER_BINDPATH:+$APPTAINER_BINDPATH,}$bindings"
if [[ -n ${SINGULARITY_BIND:-} ]]; then export SINGULARITY_BIND="$SINGULARITY_BIND,$bindings"; fi
if [[ -n ${APPTAINER_BIND:-} ]]; then export APPTAINER_BIND="$APPTAINER_BIND,$bindings"; fi
unset SINGULARITYENV_PYTHONPATH APPTAINERENV_PYTHONPATH
sha256sum "$PYTHONDS_CONTAINER" > "$dest/container.sha256"
pyds-exec python -c 'import sys; assert sys.version_info[:2] == (3,12), sys.version; print(sys.version)'
pyds-exec python -m pip --isolated install --no-index --no-deps --no-compile \
    --target /opt/openeye-install/python "/opt/openeye-source/$(basename -- "${wheels[0]}")"
mkdir -p "$dest/bin" "$dest/share/openeye"
install -m 755 "$src/openeye-pyds-exec" "$dest/bin/openeye-pyds-exec"
install -m 644 "$src/verify.py" "$dest/share/openeye/verify.py"
