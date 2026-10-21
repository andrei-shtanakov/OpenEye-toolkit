import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


WRAPPER = Path(__file__).resolve().parents[1] / 'payload/openeye-pyds-exec'


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'installation with spaces'
        (self.root / 'bin').mkdir(parents=True)
        (self.root / 'python/openeye').mkdir(parents=True)
        self.wrapper = self.root / 'bin/openeye-pyds-exec'
        shutil.copyfile(WRAPPER, self.wrapper)
        self.license = Path(self.tmp.name) / 'license dir/oe_license.txt'
        self.license.parent.mkdir()
        self.license.write_text('test fixture')
        stub = Path(self.tmp.name) / 'pyds-exec'
        stub.write_text('#!/usr/bin/env python3\nimport json, os, sys\n'
                        'print(json.dumps({"argv": sys.argv[1:], "env": dict(os.environ)}))\n')
        stub.chmod(0o755)
        self.env = {
            'PATH': f'{self.tmp.name}:{os.environ["PATH"]}',
            'PYTHONDS_VERSION': 'v1.6',
            'PYTHONDS_CONTAINER': '/image.sif',
            'OE_LICENSE': str(self.license),
        }

    def run_wrapper(self, *args):
        return subprocess.run(['bash', str(self.wrapper), *args], env=self.env,
                              capture_output=True, text=True)

    def test_forwarding_bind_and_environment(self):
        self.env.update(SINGULARITY_BIND='/existing:/existing:ro',
                        APPTAINER_BINDPATH='/data:/data',
                        APPTAINERENV_PYTHONPATH='/wrong')
        args = ['python', '-c', 'print("spaces and $literal")', '']
        result = self.run_wrapper(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['argv'], args)
        env = data['env']
        binding = f'{self.root}:/opt/openeye-toolkits:ro'
        self.assertIn(binding, env['SINGULARITY_BIND'])
        self.assertIn(binding, env['APPTAINER_BINDPATH'])
        self.assertTrue(env['SINGULARITY_BIND'].startswith('/existing:/existing:ro,'))
        for prefix in ['SINGULARITYENV_', 'APPTAINERENV_']:
            self.assertEqual(env[prefix + 'PYTHONPATH'], '/opt/openeye-toolkits/python')
            self.assertEqual(env[prefix + 'OE_LICENSE'], '/opt/openeye-license/oe_license.txt')

    def test_missing_license_refuses_launch(self):
        self.license.unlink()
        result = self.run_wrapper('python')
        self.assertEqual(result.returncode, 2)
        self.assertIn('license file is not readable', result.stderr)

    def test_wrong_version_and_empty_command_refuse_launch(self):
        self.env['PYTHONDS_VERSION'] = 'v1.5'
        self.assertEqual(self.run_wrapper('python').returncode, 2)
        self.assertEqual(self.run_wrapper().returncode, 2)


if __name__ == '__main__':
    unittest.main()
