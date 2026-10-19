import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "check_package", Path(__file__).with_name("check-package.py")
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SHA = "a" * 40
IMAGE_ID = "sha256:" + "c" * 64


class PackageIsolationTests(unittest.TestCase):
    def test_start_failure_surfaces_only_validated_marker_fields(self):
        marker = (
            b'BACKEND_PACKAGE_FAILURE={"stage":"django-setup",'
            b'"exceptionClass":"RuntimeError","filename":"probe.py","line":42}'
        )
        error = subprocess.CalledProcessError(
            1,
            ["docker", "start", "--attach", "container"],
            output=b"stdout-secret\n" + marker,
            stderr=b"stderr-secret\n",
        )
        with patch.object(probe.subprocess, "check_output", side_effect=error):
            with self.assertRaises(RuntimeError) as raised:
                probe.execute(["docker", "start", "--attach", "container"])
        self.assertEqual(
            str(raised.exception),
            "Package probe failed at stage=django-setup exception=RuntimeError frame=probe.py:42",
        )
        self.assertNotIn("stdout-secret", str(raised.exception))
        self.assertNotIn("stderr-secret", str(raised.exception))

    def test_start_failure_without_valid_marker_redacts_all_output(self):
        error = subprocess.CalledProcessError(
            17,
            ["docker", "start", "--attach", "container"],
            output=b"stdout-secret",
            stderr=b"stderr-secret",
        )
        with patch.object(probe.subprocess, "check_output", side_effect=error):
            with self.assertRaises(RuntimeError) as raised:
                probe.execute(["docker", "start", "--attach", "container"])
        self.assertEqual(
            str(raised.exception),
            "Package probe failed at stage=docker-start-attach exception=CalledProcessError exit=17",
        )
        self.assertNotIn("stdout-secret", str(raised.exception))
        self.assertNotIn("stderr-secret", str(raised.exception))

    def test_failure_marker_rejects_extra_fields_invalid_values_and_duplicates(self):
        secret_payload = (
            b'BACKEND_PACKAGE_FAILURE={"stage":"django-setup",'
            b'"exceptionClass":"RuntimeError","filename":"apps.py",'
            b'"line":42,"message":"secret"}'
        )
        unsafe_filename = (
            b'BACKEND_PACKAGE_FAILURE={"stage":"django-setup",'
            b'"exceptionClass":"RuntimeError","filename":"/private/key",'
            b'"line":42}'
        )
        self.assertIsNone(probe.parse_failure_marker(secret_payload, b""))
        self.assertIsNone(probe.parse_failure_marker(unsafe_filename, b""))
        valid = (
            b'BACKEND_PACKAGE_FAILURE={"stage":"django-setup",'
            b'"exceptionClass":"RuntimeError","filename":"probe.py","line":42}'
        )
        self.assertIsNone(probe.parse_failure_marker(valid, valid))
        duplicate_key = (
            b'BACKEND_PACKAGE_FAILURE={"stage":"django-setup",'
            b'"exceptionClass":"RuntimeError","filename":"probe.py",'
            b'"filename":"probe.py","line":42}'
        )
        self.assertIsNone(probe.parse_failure_marker(duplicate_key, b""))
        secret_identifiers = (
            b'BACKEND_PACKAGE_FAILURE={"stage":"django-setup",'
            b'"exceptionClass":"SyntheticSecretTokenABC123",'
            b'"filename":"SyntheticSecretTokenABC123.py","line":42}'
        )
        self.assertIsNone(probe.parse_failure_marker(secret_identifiers, b""))

    def test_probe_failure_emitter_only_uses_controlled_frame_and_exception_names(self):
        class SyntheticSecretTokenABC123(Exception):
            pass

        safe = image_probe.safe_failure(
            SyntheticSecretTokenABC123("exception-message-secret"),
            [
                SimpleNamespace(
                    filename="/private/SyntheticSecretTokenABC123.py", lineno=98765
                ),
                SimpleNamespace(filename=image_probe.__file__, lineno=219),
            ],
        )
        self.assertEqual(
            safe,
            {
                "stage": "probe-start",
                "exceptionClass": "Exception",
                "filename": "probe.py",
                "line": 219,
            },
        )
        serialized = json.dumps(safe)
        self.assertNotIn("SyntheticSecretTokenABC123", serialized)
        self.assertNotIn("exception-message-secret", serialized)

        unknown_frame = image_probe.safe_failure(
            RuntimeError("another-secret"),
            [SimpleNamespace(filename="/private/another-secret/settings.py", lineno=7)],
        )
        self.assertEqual(unknown_frame["filename"], "unknown")
        self.assertEqual(unknown_frame["line"], 0)
        self.assertNotIn("another-secret", json.dumps(unknown_frame))

    def test_cleanup_failure_remains_a_blocking_probe_failure(self):
        calls = []

        def fake_execute(args, timeout=300):
            calls.append(args)
            if args[:3] == ["docker", "image", "inspect"]:
                return b"123456" if "{{.Size}}" in args else IMAGE_ID.encode()
            if args[:2] == ["docker", "history"]:
                return b"12.3MB\n0B\n"
            if args[:2] == ["docker", "start"]:
                raise RuntimeError("synthetic probe failure")
            if args[:3] == ["docker", "rm", "--force"]:
                raise RuntimeError("synthetic cleanup failure")
            return b""

        with patch.object(probe, "execute", fake_execute), patch.object(
            probe, "migration_tree", return_value={}
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic cleanup failure"):
                probe.run_probe("image", SHA)
        self.assertTrue(any(args[:3] == ["docker", "rm", "--force"] for args in calls))

    def test_probe_uses_image_id_no_network_and_only_disposable_mount(self):
        calls = []

        def fake_execute(args, timeout=300):
            calls.append(args)
            if args[:3] == ["docker", "image", "inspect"]:
                return b"123456" if "{{.Size}}" in args else IMAGE_ID.encode()
            if args[:2] == ["docker", "history"]:
                return b"12.3MB\n0B\n"
            if args[:2] == ["docker", "create"]:
                self.assertEqual(args[-2:], [IMAGE_ID, "/probe/probe.py"])
                self.assertIn("--read-only", args)
                self.assertEqual(args[args.index("--network") + 1], "none")
                mounts = [arg for arg in args if arg.startswith("type=bind,")]
                self.assertEqual(len(mounts), 1)
                self.assertTrue(mounts[0].endswith(",dst=/probe,readonly"))
                directory = mounts[0].split("src=", 1)[1].split(",", 1)[0]
                self.assertTrue(Path(directory, "migrations.json").is_file())
                self.assertTrue(Path(directory, "probe.py").is_file())
                return b"synthetic-container"
            if args[:2] == ["docker", "start"]:
                return b'library output\nBACKEND_PACKAGE_RECEIPT={"result":"PASS"}\n'
            if args[:2] == ["docker", "inspect"]:
                return json.dumps(
                    [
                        {
                            "Image": IMAGE_ID,
                            "State": {"ExitCode": 0, "OOMKilled": False},
                            "HostConfig": {"NetworkMode": "none"},
                        }
                    ]
                ).encode()
            return b""

        with patch.object(probe, "execute", fake_execute), patch.object(
            probe, "migration_tree", return_value={"entries": [], "digest": "synthetic"}
        ):
            receipt = probe.run_probe("mutable-tag-is-resolved-once", SHA)
        self.assertEqual(receipt["imageId"], IMAGE_ID)
        self.assertEqual(receipt["cleanup"], "PASS")
        self.assertEqual(receipt["imageExpandedBytes"], 123456)
        self.assertEqual(receipt["layerSizesHuman"], ["12.3MB", "0B"])
        self.assertTrue(any(args[:3] == ["docker", "rm", "--force"] for args in calls))

    def test_failed_probe_always_cleans_up_and_emits_no_receipt(self):
        calls = []

        def fake_execute(args, timeout=300):
            calls.append(args)
            if args[:3] == ["docker", "image", "inspect"]:
                return b"123456" if "{{.Size}}" in args else IMAGE_ID.encode()
            if args[:2] == ["docker", "history"]:
                return b"12.3MB\n0B\n"
            if args[:2] == ["docker", "start"]:
                raise RuntimeError("synthetic probe failure")
            return b""

        with patch.object(probe, "execute", fake_execute), patch.object(
            probe, "migration_tree", return_value={}
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic probe failure"):
                probe.run_probe("image", SHA)
        self.assertTrue(any(args[:3] == ["docker", "rm", "--force"] for args in calls))

    def test_source_tree_digest_agrees_with_node_contract(self):
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        actual = probe.migration_tree(sha)
        node = subprocess.check_output(
            [
                "node",
                "--input-type=module",
                "-e",
                "import {migrationTree} from './scripts/release-contract.mjs'; "
                f"console.log(JSON.stringify(migrationTree('{sha}')))",
            ]
        )
        expected = json.loads(node)
        self.assertEqual(actual["digest"], expected["digest"])
        self.assertEqual(actual["entries"], expected["entries"])
        self.assertTrue(
            any(
                name.endswith("0012_merge_20260901_000000.py")
                for name, _ in actual["entries"]
            )
        )


image_spec = importlib.util.spec_from_file_location(
    "package_in_image", Path(__file__).with_name("package-in-image.py")
)
image_probe = importlib.util.module_from_spec(image_spec)
image_spec.loader.exec_module(image_probe)


class CPUProfileTests(unittest.TestCase):
    def torch(self, version="2.14.1+cpu", cuda=None, available=False):
        return SimpleNamespace(
            __version__=version,
            version=SimpleNamespace(cuda=cuda),
            cuda=SimpleNamespace(is_available=lambda: available),
        )

    def test_only_cpu_torch_without_cuda_packages_passes(self):
        actual = image_probe.cpu_profile(
            self.torch(), {"torch": "2.14.1+cpu", "numpy": "1.26.4"}
        )
        self.assertEqual(actual["version"], "2.14.1+cpu")
        self.assertEqual(actual["forbiddenDistributions"], [])
        for torch in [
            self.torch(version="2.14.1"),
            self.torch(cuda="13.0"),
            self.torch(available=True),
        ]:
            with self.assertRaises(AssertionError):
                image_probe.cpu_profile(torch, {})
        for package in ["nvidia-cublas", "NVIDIA_CUDNN_CU13", "cuda-toolkit", "triton"]:
            with self.assertRaises(AssertionError):
                image_probe.cpu_profile(self.torch(), {package: "synthetic"})

    def test_component_content_sizes_skip_huggingface_symlink_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "blob").write_bytes(b"1234567")
            (root / "snapshot").symlink_to(root / "blob")
            self.assertEqual(image_probe.regular_file_bytes(root), 7)


if __name__ == "__main__":
    unittest.main()
