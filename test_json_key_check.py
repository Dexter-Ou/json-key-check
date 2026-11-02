import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from json_key_check import inspect_bytes, InvalidInput, MAX_BYTES


class CoreTests(unittest.TestCase):
    def test_baseline_data_loss_and_detection(self):
        raw = b'{"service":{"port":8000,"port":9000}}'
        self.assertEqual(json.loads(raw), {"service": {"port": 9000}})
        self.assertEqual(inspect_bytes(raw)["findings"],
                         [{"pointer": "/service/port", "occurrences": 2}])

    def test_discarded_subtree_and_arrays(self):
        report = inspect_bytes(b'{"x":{"hidden":1,"hidden":2},"x":[{"v":1,"v":2}]}')
        self.assertEqual(report["duplicate_groups"], 3)
        self.assertEqual([f["pointer"] for f in report["findings"]],
                         ["/x", "/x/hidden", "/x/0/v"])

    def test_decoded_names_and_pointer_escaping(self):
        report = inspect_bytes(b'{"a":0,"\\u0061":1,"/~":2,"/~":3}')
        self.assertEqual([f["pointer"] for f in report["findings"]], ["/a", "/~1~0"])

    def test_valid_scalars_large_numbers_and_case(self):
        for raw in [b'null', b'[]', b'1e9999', b'9'*5000,
                    b'{"A":1,"a":2}', b'"text"', b'\xef\xbb\xbf{}']:
            self.assertEqual(inspect_bytes(raw)["status"], "clean")

    def test_invalid_inputs(self):
        for raw in [b'{', b'{}{}', b'{"a":1,}', b'NaN', b'Infinity', b'-Infinity', b'\xff']:
            with self.subTest(raw=raw), self.assertRaises(InvalidInput):
                inspect_bytes(raw)

    def test_limits_and_truncation(self):
        with self.assertRaisesRegex(InvalidInput, 'size_limit'):
            inspect_bytes(b' ' * (MAX_BYTES + 1))
        with self.assertRaisesRegex(InvalidInput, 'depth_limit'):
            inspect_bytes(b'['*66+b']'*66)
        report = inspect_bytes(('{' + ','.join('"k%d":0,"k%d":1' % (i,i)
                                  for i in range(103)) + '}').encode())
        self.assertEqual(report["duplicate_groups"], 103)
        self.assertEqual(len(report["findings"]), 100)
        self.assertTrue(report["findings_truncated"])

    def test_fresh_cli_status_privacy_and_input_integrity(self):
        script = str(Path(__file__).with_name('json_key_check.py').resolve())
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'input.json'
            for raw, code, status in [(b'{"x":"SECRET_VALUE","x":1}', 1, 'duplicates'),
                                      (b'{}', 0, 'clean'), (b'{"private', 2, 'error')]:
                target.write_bytes(raw)
                before = hashlib.sha256(raw).hexdigest()
                result = subprocess.run([sys.executable, script, str(target)],
                                        cwd=folder, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)['status'], status)
                self.assertNotIn(b'SECRET_VALUE', result.stdout + result.stderr)
                self.assertNotIn(str(target).encode(), result.stdout + result.stderr)
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), before)
            result = subprocess.run([sys.executable, script, str(target)+'-missing'],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['error'], 'input_io')

    def test_readme_examples(self):
        folder = Path(__file__).parent
        for name, code in [('duplicate', 1), ('clean', 0)]:
            run = subprocess.run([sys.executable, 'json_key_check.py',
                                  'examples/'+name+'.json'], cwd=folder,
                                 capture_output=True, timeout=10)
            self.assertEqual(run.returncode, code)
            self.assertIn(json.loads(run.stdout)['status'], ['clean', 'duplicates'])


if __name__ == '__main__':
    unittest.main()
