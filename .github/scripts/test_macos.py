"""Check macOS health and display startup without host devices or credentials."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from image import ROOT


class MacosRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.environment = dict(
            os.environ,
            PATH=f"{self.root}{os.pathsep}{os.environ['PATH']}",
            REIMS_CTL_DATA_DIR=str(self.root),
            XDG_RUNTIME_DIR=str(self.root),
        )
        self.pidfile = self.root / "vms/mac/qemu.pid"
        self.pidfile.parent.mkdir(parents=True)
        self.command("curl", "exit 0")

    def command(self, name, script):
        path = self.root / name
        path.write_text(f"#!/bin/sh\n{script}\n")
        path.chmod(0o755)

    def run_script(self, name):
        return subprocess.run(
            ["bash", str(ROOT / "macos" / name)],
            check=False,
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_health_requires_live_vm_and_streaming_endpoint(self):
        self.assertNotEqual(self.run_script("health.sh").returncode, 0)
        self.pidfile.touch()
        self.assertNotEqual(self.run_script("health.sh").returncode, 0)
        process = subprocess.Popen(["sleep", "30"])
        try:
            self.pidfile.write_text(str(process.pid))
            self.assertEqual(self.run_script("health.sh").returncode, 0)
            self.command("curl", "exit 22")
            self.assertNotEqual(self.run_script("health.sh").returncode, 0)
            self.command("curl", "exit 0")
        finally:
            process.terminate()
            process.wait()
        self.assertNotEqual(self.run_script("health.sh").returncode, 0)

    def test_unavailable_display_fails_startup(self):
        (self.root / "container-env").write_text("SELKIES_WAYLAND=false\n")
        self.command("timeout", "exit 1")
        self.command("sleep", "exit 0")
        result = self.run_script("run-vm.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("X display did not become ready", result.stderr)
