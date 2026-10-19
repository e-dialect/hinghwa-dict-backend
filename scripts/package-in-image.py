"""Synthetic image-only probe; invoked in a network-none disposable container."""

import hashlib
import json
import os
import importlib.metadata
import stat
import subprocess
import sys
from pathlib import Path


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def cpu_profile(torch, packages):
    assert torch.__version__ == "2.14.1+cpu", "Unexpected release torch version"
    assert torch.version.cuda is None, "CUDA build is not a CPU release"
    assert not torch.cuda.is_available(), "CUDA must be unavailable"
    forbidden = sorted(
        name
        for name in packages
        if name.lower().replace("_", "-").startswith(("nvidia-", "cuda-", "triton"))
    )
    assert not forbidden, "CUDA/Triton packages must not be installed"
    return {
        "version": torch.__version__,
        "cuda": torch.version.cuda,
        "cudaAvailable": False,
        "forbiddenDistributions": forbidden,
    }


def regular_file_bytes(directory):
    # Apparent component content size, not a disk usage/capacity guarantee.
    # Skip symlinks so the HF snapshot links do not double-count its blobs.
    return sum(
        entry.lstat().st_size
        for entry in Path(directory).rglob("*")
        if stat.S_ISREG(entry.lstat().st_mode)
    )


def main():
    expected = json.loads(Path("/probe/migrations.json").read_text())
    actual = []
    root = Path("/usr/src/HinghwaDict-backend")
    for name, checksum in expected["entries"]:
        target = root / name
        assert target.is_relative_to(root) and ".." not in target.parts
        content_hash = digest(target.read_bytes())
        assert content_hash == checksum, "Image migration differs from source"
        actual.append([name, content_hash])
    assert (
        digest(json.dumps(actual, separators=(",", ":")).encode()) == expected["digest"]
    )
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "HinghwaDict.settings"
    sys.path.insert(0, str(root))
    # Import the image's settings, then override only disposable probe storage/logging.
    # Never import a production environment/configuration or expose credentials.
    import HinghwaDict.settings as settings

    settings.DATABASES["default"]["NAME"] = "/tmp/package-smoke.sqlite3"
    settings.MEDIA_ROOT = "/tmp/package-media"
    settings.SAVED_PINYIN = "/tmp/package-audio"
    settings.SEMANTIC_SEARCH_DATA_DIR = "/tmp/package-semantic"
    settings.LOGGING = {"version": 1, "disable_existing_loggers": False}
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert settings.SEMANTIC_SEARCH_MODEL_NAME == "BAAI/bge-small-zh-v1.5"
    assert (
        settings.SEMANTIC_SEARCH_MODEL_REVISION
        == "7999e1d3359715c523056ef9478215996d62a620"
    )
    snapshot = (
        Path(settings.SEMANTIC_SEARCH_MODEL_CACHE)
        / "models--BAAI--bge-small-zh-v1.5/snapshots"
        / settings.SEMANTIC_SEARCH_MODEL_REVISION
    )
    assert snapshot.is_dir(), "Pinned model snapshot absent from image"

    import django

    django.setup()
    assert django.get_version() == "5.0.3"
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.contrib.auth import get_user_model
    from word.search.encoder import BGEEncoder
    import numpy as np
    import torch

    packages = {
        distribution.metadata["Name"]: distribution.version
        for distribution in importlib.metadata.distributions()
    }
    cpu = cpu_profile(torch, packages)
    subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        check=True,
        capture_output=True,
        timeout=60,
    )
    components = {
        "versions": {
            name: importlib.metadata.version(name)
            for name in [
                "torch",
                "sentence-transformers",
                "transformers",
                "numpy",
                "faiss-cpu",
                "django",
            ]
        },
        "regularFileBytesNoSymlinks": {
            "torch": regular_file_bytes(Path(torch.__file__).parent),
            "semanticModelCache": regular_file_bytes(
                settings.SEMANTIC_SEARCH_MODEL_CACHE
            ),
            "static": regular_file_bytes("/static"),
        },
    }

    assert not Path("/tmp/package-smoke.sqlite3").exists()
    call_command("migrate", interactive=False, verbosity=0)
    executor = MigrationExecutor(connection)
    assert not executor.migration_plan(executor.loader.graph.leaf_nodes())
    user = get_user_model().objects.create_user(
        username="package_synthetic_user", password="synthetic-only-password"
    )
    user.refresh_from_db()
    assert user.check_password("synthetic-only-password")
    user.delete()
    with connection.cursor() as cursor:
        assert cursor.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    vector = BGEEncoder().encode_query("synthetic package smoke")
    assert vector.shape == (512,) and np.isfinite(vector).all()
    assert float(np.linalg.norm(vector)) > 0
    connection.close()
    result = {
        "result": "PASS",
        "torchCPU": cpu,
        "dependenciesConsistent": True,
        "components": components,
        "migrationTreeDigest": expected["digest"],
        "djangoVersion": django.get_version(),
        "semanticModel": {
            "name": settings.SEMANTIC_SEARCH_MODEL_NAME,
            "revision": settings.SEMANTIC_SEARCH_MODEL_REVISION,
        },
        "modelLoadedOffline": True,
        "emptySQLiteMigrated": True,
        "sqliteIntegrity": True,
        "syntheticUserRoundtrip": True,
        "noPendingMigrations": True,
        "productionDataUsed": False,
    }
    print("BACKEND_PACKAGE_RECEIPT=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
