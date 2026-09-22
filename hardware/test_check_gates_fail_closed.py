"""Fail-closed regression tests for the two pre-merge geometry gates.

The fake OpenSCAD executable makes failures deterministic without requiring CAD
models or a local OpenSCAD installation. It deliberately emits plausible stale
ECHO output for some failed compilations, because that is the dangerous case.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HARDWARE = Path(__file__).resolve().parent


def load_gate(name: str):
    spec = importlib.util.spec_from_file_location(name, HARDWARE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FIT = load_gate("check_fit_geometry")
CROSS = load_gate("check_cross_branch")

FAKE_OPENSCAD = '''#!{python}
import os
from pathlib import Path
import sys
import time

mode = os.environ["FAKE_OPENSCAD_MODE"]
out = Path(sys.argv[sys.argv.index("-o") + 1])
if mode == "hang":
    time.sleep(10)
if mode in ("unknown", "nonzero_empty", "nonzero_solid", "partial", "stale_contract", "fit_valid"):
    # A real, nonempty STL: a gate must fail because of the diagnostic/contract,
    # not merely because the fake compiler neglected to create its output.
    out.write_text("""solid stub
facet normal 0 0 1
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 1 0
 endloop
endfacet
endsolid stub
""")
if mode == "unknown":
    print("WARNING: Ignoring unknown module 'shell_front' in file", file=sys.stderr)
    print("Vertices: 3", file=sys.stderr)
elif mode == "nonzero_empty":
    print("Current top level object is empty.", file=sys.stderr)
    sys.exit(7)
elif mode == "nonzero_solid":
    print("Vertices: 3", file=sys.stderr)
    sys.exit(7)
elif mode == "fit_valid":
    source = Path(sys.argv[-1]).read_text()
    if ("translate([0,-0.20,0]) modsolid()" in source or
            "translate([0,-0.10,0]) top_frame()" in source):
        print("Vertices: 3", file=sys.stderr)
    else:
        out.unlink()
        print("Current top level object is empty.", file=sys.stderr)
elif mode in ("partial", "stale_contract", "full_contract"):
    for key in os.environ["FAKE_CONTRACT_KEYS"].split(","):
        print('ECHO: "ICD-CONTRACT|{{}}|0"'.format(key), file=sys.stderr)
    if mode == "stale_contract":
        sys.exit(7)
elif mode == "no_output":
    pass
else:
    raise ValueError(mode)
'''


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.openscad = self.bin / "openscad"
        self.openscad.write_text(FAKE_OPENSCAD.format(python=sys.executable))
        self.openscad.chmod(0o755)
        self.module = self.root / "module.scad"
        self.dock = self.root / "dock.scad"
        self.module.write_text("module shell_front() {}\n")
        self.dock.write_text("module handheld_all() {}\n")
        self.env = os.environ.copy()
        self.env["PATH"] = str(self.bin) + os.pathsep + self.env.get("PATH", "")

    def env_for(self, mode: str, keys=()):
        env = self.env.copy()
        env["FAKE_OPENSCAD_MODE"] = mode
        env["FAKE_CONTRACT_KEYS"] = ",".join(keys)
        return env

    def fit_run(self, mode: str, timeout_s=0.5):
        with mock.patch.dict(os.environ, self.env_for(mode), clear=True):
            return FIT.run(str(self.root), str(self.module), str(self.dock),
                           "intersection(){ handheld_all(); mos(); }", timeout_s)

    def gate_cli(self, filename: str, mode: str, keys=()):
        return subprocess.run(
            [sys.executable, str(HARDWARE / filename),
             "--module", str(self.module), "--dock", str(self.dock)],
            capture_output=True, text=True, timeout=5,
            env=self.env_for(mode, keys),
        )

    def test_fit_unknown_module_blocks_entire_gate(self):
        result = self.gate_cli("check_fit_geometry.py", "unknown")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("全部通过", result.stdout)

    def test_fit_nonzero_exit_rejects_stale_empty_and_solid_markers(self):
        for mode in ("nonzero_empty", "nonzero_solid"):
            with self.subTest(mode=mode):
                got, info = self.fit_run(mode)
                self.assertEqual(got, "error", (got, info))

    def test_fit_no_stl_or_result_marker_is_not_empty_geometry(self):
        got, info = self.fit_run("no_output")
        self.assertEqual(got, "error", (got, info))

    def test_fit_timeout_is_reported_as_error(self):
        got, info = self.fit_run("hang", timeout_s=0.15)
        self.assertEqual(got, "error", (got, info))
        self.assertIn("0.15", info)

    def test_fit_all_decisive_results_can_pass(self):
        result = self.gate_cli("check_fit_geometry.py", "fit_valid")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("全部通过：15", result.stdout)

    def test_cross_branch_partial_required_contract_blocks_gate(self):
        result = self.gate_cli("check_cross_branch.py", "partial", ["MOSAICO_W"])
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("全部通过", result.stdout)

    def test_cross_branch_nonzero_exit_rejects_stale_complete_echo(self):
        keys = {key for key, *_ in CROSS.EQ}
        keys.update(key for key, *_ in CROSS.FIT)
        keys.update(key for _, key, *_ in CROSS.FIT)
        keys.update(key for key, *_ in CROSS.GE)
        result = self.gate_cli("check_cross_branch.py", "stale_contract", sorted(keys))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("全部通过", result.stdout)

    def test_cross_branch_complete_consistent_contract_can_pass(self):
        keys = {key for key, *_ in CROSS.EQ}
        keys.update(key for key, *_ in CROSS.FIT)
        keys.update(key for _, key, *_ in CROSS.FIT)
        keys.update(key for key, *_ in CROSS.GE)
        result = self.gate_cli("check_cross_branch.py", "full_contract", sorted(keys))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("实际检查：等值 16/16，包含 6/6，供需 1/1", result.stdout)


if __name__ == "__main__":
    unittest.main()
