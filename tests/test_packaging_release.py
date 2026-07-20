from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sta_lite import __version__
from sta_lite.cli import build_parser
from sta_lite.desktop import prepare_workspace
from sta_lite.resources import resource_path, resource_root
from sta_lite.review.case_registry import CASE_REGISTRY, case_registry


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PackagingReleaseTests(unittest.TestCase):
    def test_stable_version_and_cli_parser(self) -> None:
        self.assertEqual(__version__, "0.2.0")
        with self.assertRaises(SystemExit) as context:
            build_parser().parse_args(["--version"])
        self.assertEqual(context.exception.code, 0)

    def test_source_resource_root_contains_runtime_assets(self) -> None:
        self.assertEqual(resource_root(), PROJECT_ROOT)
        self.assertTrue(resource_path("sta_lite", "gui", "static", "index.html").is_file())
        self.assertTrue(resource_path("risk_profile", "cases").is_dir())
        self.assertTrue(resource_path("examples", "lint").is_dir())

    def test_desktop_workspace_is_writable_and_preserves_user_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = prepare_workspace(Path(temp_dir) / "workspace")
            example = workspace / "examples" / "counter" / "counter.v"
            self.assertTrue(example.is_file())
            example.write_text("// 用户本地修改\n", encoding="utf-8")
            prepare_workspace(workspace)
            self.assertEqual(example.read_text(encoding="utf-8"), "// 用户本地修改\n")
            self.assertTrue((workspace / "risk_profile" / "cases").is_dir())
            self.assertTrue((workspace / "runs").is_dir())

    def test_case_coverage_evidence_is_available_to_package(self) -> None:
        cases = case_registry(PROJECT_ROOT)
        self.assertEqual(len(cases), len(CASE_REGISTRY))
        self.assertTrue(all(item["verification_evidence"] for item in cases))
        bundled_roots = ("examples/", "lint/", "risk_profile/", "tests/")
        for item in CASE_REGISTRY:
            bundled = [path for path in item["test_paths"] if path.startswith(bundled_roots)]
            self.assertTrue(bundled, item["case_id"])
            self.assertTrue(any((PROJECT_ROOT / path).exists() for path in bundled), item["case_id"])

    def test_release_layout_and_build_inputs(self) -> None:
        required = [
            ".github/workflows/release.yml",
            "packaging/build_windows.ps1",
            "packaging/windows_installer.nsi",
            "packaging/build_ubuntu20.sh",
            "packaging/install_ubuntu.sh",
            "install_package/window10/README.md",
            "install_package/window11/README.md",
            "install_package/ubuntu20/README.md",
            "THIRD_PARTY_NOTICES.md",
        ]
        for relative in required:
            self.assertTrue((PROJECT_ROOT / relative).is_file(), relative)

        build_text = "\n".join(
            (PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for relative in ("packaging/build_windows.ps1", "packaging/build_ubuntu20.sh")
        )
        self.assertNotIn("nangate45", build_text)
        self.assertNotIn("tools/iverilog", build_text)
        self.assertIn("risk_profile", build_text)
        self.assertIn("sta_lite/gui/static", build_text)
        self.assertIn("$ProjectRoot", build_text)
        self.assertIn("${PROJECT_ROOT}", build_text)

    def test_case_metadata_is_json_serializable(self) -> None:
        json.dumps(case_registry(PROJECT_ROOT), ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
