"""Run inside PythonDS; add --license for runtime acceptance."""
import importlib.metadata
import os
from pathlib import Path
import sys

assert sys.version_info[:2] == (3, 12), sys.version
assert importlib.metadata.version('openeye-toolkits') == '2026.1.0'
from openeye import oechem

assert Path(oechem.__file__).resolve().is_relative_to('/opt/openeye-toolkits/python'), oechem.__file__
print('Python:', sys.version)
print('OEChem:', oechem.OEChemGetVersion())
print('Loaded from:', oechem.__file__)
if '--license' in sys.argv:
    assert Path(os.environ['OE_LICENSE']).is_file()
    assert oechem.OEChemIsLicensed(), 'OEChem license unavailable'
    mol = oechem.OEGraphMol()
    assert oechem.OESmilesToMol(mol, 'CCO')
    assert mol.NumAtoms() == 3
    print('OEChem license and molecule operation: PASS')
