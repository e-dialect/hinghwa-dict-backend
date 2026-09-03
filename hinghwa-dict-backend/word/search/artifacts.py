from __future__ import annotations

import ast
import hashlib
import json
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from django.conf import settings

from word.models import Word

from .encoder import BGEEncoder
from .exceptions import SearchUnavailable

MANIFEST_SCHEMA_VERSION = 1


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _parse_string_list(raw_value: str) -> list[str]:
    if not raw_value:
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(raw_value)
        except (TypeError, ValueError, SyntaxError, json.JSONDecodeError):
            continue
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [raw_value.strip()] if raw_value.strip() else []


def export_visible_entries() -> list[dict]:
    queryset = (
        Word.objects.filter(visibility=True)
        .order_by("id")
        .values(
            "id",
            "word",
            "definition",
            "annotation",
            "mandarin",
            "standard_ipa",
            "standard_pinyin",
        )
    )
    entries = []
    for item in queryset:
        entries.append(
            {
                "id": int(item["id"]),
                "word": str(item["word"] or "").strip(),
                "definition": str(item["definition"] or "").strip(),
                "annotation": str(item["annotation"] or "").strip(),
                "mandarin": _parse_string_list(item["mandarin"]),
                "standard_ipa": str(item["standard_ipa"] or "").strip(),
                "standard_pinyin": str(item["standard_pinyin"] or "").strip(),
            }
        )
    return entries


def _get_faiss():
    import faiss

    return faiss


def _write_bytes_atomically(path: Path, content: bytes) -> None:
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary_path.open("wb") as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary_path, path)


def _safe_artifact_path(data_dir: Path, filename: str) -> Path:
    if not filename or Path(filename).name != filename:
        raise SearchUnavailable("semantic index manifest contains an unsafe path")
    return data_dir / filename


def _cleanup_generations(data_dir: Path, keep: set[str]) -> None:
    for pattern in ("entries-*.json", "index-*.faiss"):
        for path in data_dir.glob(pattern):
            if path.name not in keep:
                path.unlink(missing_ok=True)


def manifest_matches_configuration(manifest: dict) -> bool:
    return (
        manifest.get("schema_version") == MANIFEST_SCHEMA_VERSION
        and manifest.get("model_name") == settings.SEMANTIC_SEARCH_MODEL_NAME
        and manifest.get("model_revision") == settings.SEMANTIC_SEARCH_MODEL_REVISION
    )


def publish_semantic_manifest(
    manifest: dict,
    *,
    data_dir: str | Path | None = None,
) -> None:
    artifact_dir = Path(data_dir or settings.SEMANTIC_SEARCH_DATA_DIR)
    manifest_path = artifact_dir / "manifest.json"
    previous_names: set[str] = set()
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous_names.update(
                [previous.get("entries_file", ""), previous.get("index_file", "")]
            )
        except (OSError, ValueError):
            previous_names.clear()

    _write_bytes_atomically(manifest_path, _canonical_json_bytes(manifest))
    _cleanup_generations(
        artifact_dir,
        {
            manifest["entries_file"],
            manifest["index_file"],
            *[name for name in previous_names if name],
        },
    )


def build_semantic_artifacts(
    revision: int,
    *,
    encoder: BGEEncoder | None = None,
    data_dir: str | Path | None = None,
    publish: bool = True,
) -> dict:
    encoder = encoder or BGEEncoder()
    artifact_dir = Path(data_dir or settings.SEMANTIC_SEARCH_DATA_DIR)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    entries = export_visible_entries()
    vectors = encoder.encode_entries(entries)
    if vectors.shape != (len(entries), encoder.dimension):
        raise ValueError(
            f"encoder returned {vectors.shape}, expected {(len(entries), encoder.dimension)}"
        )

    faiss = _get_faiss()
    index = faiss.IndexFlatIP(encoder.dimension)
    if entries:
        index.add(np.ascontiguousarray(vectors, dtype=np.float32))

    generation = uuid.uuid4().hex
    entries_name = f"entries-{generation}.json"
    index_name = f"index-{generation}.faiss"
    entries_path = artifact_dir / entries_name
    index_path = artifact_dir / index_name
    temporary_index_path = artifact_dir / f".{index_name}.tmp"

    entries_bytes = _canonical_json_bytes(entries)
    _write_bytes_atomically(entries_path, entries_bytes)
    faiss.write_index(index, str(temporary_index_path))
    os.replace(temporary_index_path, index_path)
    index_sha256 = hashlib.sha256(index_path.read_bytes()).hexdigest()

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generation": generation,
        "revision": int(revision),
        "entry_count": len(entries),
        "vector_dimension": encoder.dimension,
        "entries_file": entries_name,
        "entries_sha256": hashlib.sha256(entries_bytes).hexdigest(),
        "index_file": index_name,
        "index_sha256": index_sha256,
        "model_name": settings.SEMANTIC_SEARCH_MODEL_NAME,
        "model_revision": settings.SEMANTIC_SEARCH_MODEL_REVISION,
    }
    if publish:
        publish_semantic_manifest(manifest, data_dir=artifact_dir)
    return manifest


@dataclass(frozen=True)
class ArtifactBundle:
    manifest: dict
    entries: list[dict]
    index: Any


class ArtifactRepository:
    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir or settings.SEMANTIC_SEARCH_DATA_DIR)
        self._generation = None
        self._bundle = None
        self._lock = threading.Lock()

    def load(self) -> ArtifactBundle:
        manifest_path = self.data_dir / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SearchUnavailable("semantic index manifest is unavailable") from exc

        if not manifest_matches_configuration(manifest):
            raise SearchUnavailable("semantic index manifest configuration is stale")
        generation = manifest.get("generation")
        if not generation:
            raise SearchUnavailable("semantic index manifest has no generation")

        with self._lock:
            if generation == self._generation and self._bundle is not None:
                return self._bundle

            entries_path = _safe_artifact_path(
                self.data_dir, manifest.get("entries_file", "")
            )
            index_path = _safe_artifact_path(
                self.data_dir, manifest.get("index_file", "")
            )
            try:
                entries_bytes = entries_path.read_bytes()
                index_bytes = index_path.read_bytes()
                entries = json.loads(entries_bytes.decode("utf-8"))
                index = _get_faiss().read_index(str(index_path))
            except (OSError, ValueError, RuntimeError) as exc:
                raise SearchUnavailable(
                    "semantic index artifacts are unreadable"
                ) from exc

            if hashlib.sha256(entries_bytes).hexdigest() != manifest.get(
                "entries_sha256"
            ):
                raise SearchUnavailable("semantic entry snapshot checksum mismatch")
            if hashlib.sha256(index_bytes).hexdigest() != manifest.get("index_sha256"):
                raise SearchUnavailable("FAISS index checksum mismatch")
            if not isinstance(entries, list) or len(entries) != manifest.get(
                "entry_count"
            ):
                raise SearchUnavailable("semantic entry snapshot count mismatch")
            if index.ntotal != len(entries) or index.d != manifest.get(
                "vector_dimension"
            ):
                raise SearchUnavailable("FAISS index metadata does not match manifest")

            self._generation = generation
            self._bundle = ArtifactBundle(manifest, entries, index)
            return self._bundle


repository = ArtifactRepository()
