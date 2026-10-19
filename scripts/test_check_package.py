import importlib.util
import json
from pathlib import Path
import subprocess
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
    def test_probe_uses_image_id_no_network_and_only_disposable_mount(self):
        calls = []

        def fake_execute(args, timeout=300):
            calls.append(args)
            if args[:3] == ["docker", "image", "inspect"]:
                return IMAGE_ID.encode()
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
        self.assertTrue(any(args[:3] == ["docker", "rm", "--force"] for args in calls))

    def test_failed_probe_always_cleans_up_and_emits_no_receipt(self):
        calls = []

        def fake_execute(args, timeout=300):
            calls.append(args)
            if args[:3] == ["docker", "image", "inspect"]:
                return IMAGE_ID.encode()
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


if __name__ == "__main__":
    unittest.main()
