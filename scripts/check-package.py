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


FAILURE_MARKER = b"BACKEND_PACKAGE_FAILURE="
FAILURE_STAGES = {
    "probe-start",
    "read-migration-manifest",
    "verify-migrations",
    "import-settings",
    "configure-synthetic-settings",
    "verify-model-snapshot",
    "django-setup",
    "verify-runtime",
    "migrate-synthetic-sqlite",
    "semantic-model-smoke",
    "build-receipt",
}


def parse_failure_marker(stdout, stderr):
    candidates = []
    for stream in (stdout, stderr):
        if not isinstance(stream, bytes):
            continue
        for line in stream[-65536:].splitlines():
            if line.startswith(FAILURE_MARKER) and len(line) <= 512:
                candidates.append(line[len(FAILURE_MARKER) :])
    if len(candidates) != 1:
        return None
    try:
        payload = json.loads(candidates[0].decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or set(payload) != {
        "stage",
        "exceptionClass",
        "filename",
        "line",
    }:
        return None
    stage = payload["stage"]
    exception_class = payload["exceptionClass"]
    filename = payload["filename"]
    line = payload["line"]
    if not isinstance(stage, str) or stage not in FAILURE_STAGES:
        return None
    if not isinstance(exception_class, str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_]{0,79}", exception_class
    ):
        return None
    if (
        not isinstance(filename, str)
        or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", filename)
        or filename in {".", ".."}
    ):
        return None
    if isinstance(line, bool) or not isinstance(line, int) or not 0 <= line <= 10_000_000:
        return None
    return {
        "stage": stage,
        "exceptionClass": exception_class,
        "filename": filename,
        "line": line,
    }


def execute(args, timeout=300):
    try:
        return subprocess.check_output(args, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.CalledProcessError as exc:
        if args[:2] == ["docker", "start"]:
            failure = parse_failure_marker(exc.output, exc.stderr)
            if failure:
                raise RuntimeError(
                    "Package probe failed at stage={} exception={} frame={}:{}".format(
                        failure["stage"],
                        failure["exceptionClass"],
                        failure["filename"],
                        failure["line"],
                    )
                ) from None
            raise RuntimeError(
                "Package probe failed at stage=docker-start-attach exception=CalledProcessError exit={}"
                .format(exc.returncode)
            ) from None
        raise RuntimeError(
            "Package probe operation failed; diagnostics withheld"
        ) from None
    except (subprocess.SubprocessError, OSError) as exc:
        if args[:2] == ["docker", "start"]:
            exception_class = type(exc).__name__
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", exception_class):
                exception_class = "SubprocessError"
            raise RuntimeError(
                "Package probe failed at stage=docker-start-attach exception={}".format(
                    exception_class
                )
            ) from None
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
    image_expanded_bytes = int(
        execute(["docker", "image", "inspect", "--format", "{{.Size}}", image_id])
    )
    assert image_expanded_bytes > 0, "Missing actual expanded image size"
    history_sizes = (
        execute(["docker", "history", "--no-trunc", "--format", "{{.Size}}", image_id])
        .decode()
        .splitlines()
    )
    assert history_sizes, "Missing actual layer size evidence"
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
        {
            "cleanup": "PASS",
            "sourceSHA": sha,
            "imageId": image_id,
            "network": "none",
            "imageExpandedBytes": image_expanded_bytes,
            "layerSizesHuman": history_sizes,
        }
    )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    print(json.dumps(run_probe(args.image, args.source_sha), sort_keys=True))
