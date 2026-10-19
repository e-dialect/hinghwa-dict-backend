"""Smoke only the exact CI image; all state lives in private disposable tmpfs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid


def execute(args, timeout=300):
    try:
        return subprocess.check_output(args, stderr=subprocess.PIPE, timeout=timeout)
    except (subprocess.SubprocessError, OSError):
        raise RuntimeError(
            "Package probe operation failed; diagnostics withheld"
        ) from None


def migration_tree(sha):
    names = execute(["git", "ls-tree", "-rz", "--name-only", sha]).decode().split("\0")
    entries = []
    prefix = "hinghwa-dict-backend/"
    for name in sorted(names):
        if name.startswith(prefix) and "/migrations/" in name:
            content = execute(["git", "show", f"{sha}:{name}"])
            checksum = "sha256:" + hashlib.sha256(content).hexdigest()
            entries.append([name[len(prefix) :], checksum])
    assert entries, "No tracked migration files"
    canonical = json.dumps(entries, separators=(",", ":")).encode()
    return {
        "entries": entries,
        "digest": "sha256:" + hashlib.sha256(canonical).hexdigest(),
    }


def run_probe(image, sha):
    assert re.fullmatch("[0-9a-f]{40}", sha)
    image_id = (
        execute(["docker", "image", "inspect", "--format", "{{.Id}}", image])
        .decode()
        .strip()
    )
    assert re.fullmatch("sha256:[0-9a-f]{64}", image_id)
    name = "backend-package-" + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="backend-package-") as directory:
        os.chmod(directory, 0o700)
        probe = Path(directory)
        (probe / "migrations.json").write_text(json.dumps(migration_tree(sha)))
        (probe / "probe.py").write_bytes(
            Path(__file__).with_name("package-in-image.py").read_bytes()
        )
        try:
            execute(
                [
                    "docker",
                    "create",
                    "--name",
                    name,
                    "--network",
                    "none",
                    "--read-only",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges:true",
                    "--memory",
                    "3g",
                    "--memory-swap",
                    "3g",
                    "--cpus",
                    "2",
                    "--pids-limit",
                    "256",
                    "--tmpfs",
                    "/tmp:rw,nosuid,size=512m",
                    "--mount",
                    f"type=bind,src={directory},dst=/probe,readonly",
                    "--env",
                    "DEBUG=false",
                    "--env",
                    "SECRET_KEY=synthetic-package-smoke-only-not-production",
                    "--env",
                    "HF_HUB_OFFLINE=1",
                    "--env",
                    "TRANSFORMERS_OFFLINE=1",
                    "--workdir",
                    "/usr/src/HinghwaDict-backend",
                    "--entrypoint",
                    "python",
                    image_id,
                    "/probe/probe.py",
                ]
            )
            output = execute(
                ["docker", "start", "--attach", name], timeout=600
            ).decode()
            state = json.loads(execute(["docker", "inspect", name]))[0]
            assert state["State"]["ExitCode"] == 0 and not state["State"]["OOMKilled"]
            assert state["Image"] == image_id
            assert state["HostConfig"]["NetworkMode"] == "none"
            receipts = [
                line.split("=", 1)[1]
                for line in output.splitlines()
                if line.startswith("BACKEND_PACKAGE_RECEIPT=")
            ]
            assert len(receipts) == 1
            receipt = json.loads(receipts[0])
        finally:
            execute(["docker", "rm", "--force", name])
            remaining = execute(
                ["docker", "ps", "--all", "--quiet", "--filter", f"name=^/{name}$"]
            )
            assert not remaining.strip(), "Probe container cleanup failed"
    receipt.update(
        {"cleanup": "PASS", "sourceSHA": sha, "imageId": image_id, "network": "none"}
    )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    print(json.dumps(run_probe(args.image, args.source_sha), sort_keys=True))
