"""Safely import human-reviewed terms from the kinship graph inventory."""

import json
from collections import Counter
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from word.models import Word, split


REQUIRED_CONFIRMED_FIELDS = ("word", "definition", "standard_ipa", "standard_pinyin")
WORD_MAX_LENGTHS = {"word": 60, "standard_ipa": 100, "standard_pinyin": 100}
JSON_STRING_LIST_FIELDS = ("mandarin", "tags")
DEFAULT_CATALOG = (
    Path(__file__).resolve().parents[2] / "data" / "relative_graph_entries.json"
)


def load_catalog(path):
    try:
        with open(path, encoding="utf-8") as catalog_file:
            catalog = json.load(catalog_file)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CommandError("Cannot read catalog {}: {}".format(path, exc))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("entries"), list):
        raise CommandError("Catalog must be an object containing an entries array.")
    return catalog


def entry_error(entry):
    if not isinstance(entry, dict):
        return "entry is not an object"
    if not isinstance(entry.get("word"), str) or not entry["word"].strip():
        return "missing word"
    if entry.get("status") not in ("confirmed", "pending", "existing"):
        return "status must be confirmed, pending, or existing"
    optional_strings = ("annotation", "mandarin", "tags", "reason", "relationship")
    invalid_optional = [
        field
        for field in optional_strings
        if field in entry and not isinstance(entry[field], str)
    ]
    if invalid_optional:
        return "fields must be strings: {}".format(", ".join(invalid_optional))
    if "database_id" in entry and (
        isinstance(entry["database_id"], bool)
        or not isinstance(entry["database_id"], int)
        or entry["database_id"] < 1
    ):
        return "database_id must be a positive integer"
    if entry["status"] == "existing" and "database_id" not in entry:
        return "existing entry requires database_id for runtime verification"
    if entry.get("status") != "confirmed":
        return None
    missing = [
        field
        for field in REQUIRED_CONFIRMED_FIELDS
        if not isinstance(entry.get(field), str) or not entry[field].strip()
    ]
    if missing:
        return "confirmed entry is missing {}".format(", ".join(missing))
    if not isinstance(entry.get("evidence"), str) or not entry["evidence"].strip():
        return "confirmed entry is missing evidence"
    normalized_lengths = {
        "word": entry["word"].strip(),
        "standard_ipa": split(entry["standard_ipa"].strip()),
        "standard_pinyin": split(entry["standard_pinyin"].strip()),
    }
    too_long = [
        field
        for field, limit in WORD_MAX_LENGTHS.items()
        if len(normalized_lengths[field]) > limit
    ]
    if too_long:
        return "fields exceed model maximum length: {}".format(", ".join(too_long))
    for field in JSON_STRING_LIST_FIELDS:
        raw_value = entry.get(field, "[]")
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            return "{} must contain a JSON array of strings".format(field)
        if not isinstance(parsed, list) or not all(
            isinstance(value, str) for value in parsed
        ):
            return "{} must contain a JSON array of strings".format(field)
    return None


class Command(BaseCommand):
    help = (
        "Validate or import human-confirmed kinship terms. Defaults to dry-run; "
        "it never alters an existing Word."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--catalog",
            default=str(DEFAULT_CATALOG),
            help="Path to a reviewed JSON catalog.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Create eligible entries (otherwise dry-run).",
        )
        parser.add_argument(
            "--contributor-id",
            type=int,
            help="Required with --apply; existing auth_user id.",
        )
        parser.add_argument(
            "--json", action="store_true", help="Emit the report as JSON."
        )

    def handle(self, *args, **options):
        if options["apply"] and not options["contributor_id"]:
            raise CommandError(
                "--apply requires --contributor-id; no account is created implicitly."
            )
        catalog = load_catalog(options["catalog"])
        entries = catalog["entries"]
        words = [
            item["word"].strip()
            for item in entries
            if isinstance(item, dict) and isinstance(item.get("word"), str)
        ]
        duplicates = {
            word for word, count in Counter(words).items() if word and count > 1
        }
        report = {
            "mode": "apply" if options["apply"] else "dry-run",
            "created": [],
            "existing": [],
            "conflict": [],
            "pending": [],
            "blocked": [],
        }

        contributor = None
        if options["apply"]:
            try:
                contributor = User.objects.get(pk=options["contributor_id"])
            except User.DoesNotExist:
                raise CommandError(
                    "Contributor {} does not exist.".format(options["contributor_id"])
                )

        candidates = []
        with transaction.atomic():
            for entry in entries:
                word = (
                    entry["word"].strip()
                    if isinstance(entry, dict) and isinstance(entry.get("word"), str)
                    else ""
                )
                error = entry_error(entry)
                if error:
                    report["conflict"].append({"word": word, "reason": error})
                    continue
                if word in duplicates:
                    report["conflict"].append(
                        {"word": word, "reason": "duplicate catalog word"}
                    )
                    continue
                if entry["status"] != "confirmed":
                    if entry["status"] == "existing":
                        current = (
                            Word.objects.filter(pk=entry["database_id"])
                            .values("id", "word")
                            .first()
                        )
                        if current is None:
                            report["conflict"].append(
                                {
                                    "word": word,
                                    "reason": "catalog existing record {} no longer exists; re-review required".format(
                                        entry["database_id"]
                                    ),
                                }
                            )
                            continue
                        if current["word"] != word:
                            report["conflict"].append(
                                {
                                    "word": word,
                                    "reason": "catalog existing id {} belongs to {!r}; re-review required".format(
                                        entry["database_id"], current["word"]
                                    ),
                                }
                            )
                            continue
                        bucket = "existing"
                    else:
                        bucket = "pending"
                    item = {
                        "word": word,
                        "reason": entry.get("reason", "needs human review"),
                    }
                    if bucket == "existing" and "database_id" in entry:
                        item["database_id"] = entry["database_id"]
                    report[bucket].append(item)
                    continue

                rows = list(
                    Word.objects.filter(word=word).values(
                        "id", "definition", "standard_ipa", "standard_pinyin"
                    )
                )
                if rows:
                    expected = {
                        "definition": entry["definition"].strip(),
                        "standard_ipa": split(entry["standard_ipa"].strip()),
                        "standard_pinyin": split(entry["standard_pinyin"].strip()),
                    }
                    same = all(
                        all(row[field] == value for field, value in expected.items())
                        for row in rows
                    )
                    bucket = "existing" if same else "conflict"
                    reason = (
                        "matching word already exists"
                        if same
                        else "word already exists with different reviewed fields"
                    )
                    report[bucket].append(
                        {
                            "word": word,
                            "ids": [row["id"] for row in rows],
                            "reason": reason,
                        }
                    )
                    continue

                planned = {
                    "word": word,
                    "relationship": entry.get("relationship"),
                    "evidence": entry["evidence"],
                }
                candidates.append((entry, planned))

            # Preflight the whole inventory before creating anything. A typo or
            # collision anywhere in the reviewed batch must not leave a partial import.
            if options["apply"] and report["conflict"]:
                report["blocked"] = [
                    {
                        "word": planned["word"],
                        "reason": "not imported because catalog conflicts were found",
                    }
                    for _entry, planned in candidates
                ]
            elif options["apply"]:
                for entry, planned in candidates:
                    created = Word.objects.create(
                        word=planned["word"],
                        definition=entry["definition"].strip(),
                        annotation=entry.get("annotation", "").strip(),
                        mandarin=entry.get("mandarin", "[]").strip() or "[]",
                        standard_ipa=entry["standard_ipa"].strip(),
                        standard_pinyin=entry["standard_pinyin"].strip(),
                        tags=entry.get("tags", "[]").strip() or "[]",
                        contributor=contributor,
                        visibility=False,
                    )
                    planned["id"] = created.id
                    report["created"].append(planned)
            else:
                report["created"] = [planned for _entry, planned in candidates]

        if options["json"]:
            self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
        else:
            for bucket in ("created", "existing", "conflict", "pending", "blocked"):
                self.stdout.write("{}: {}".format(bucket, len(report[bucket])))
                for item in report[bucket]:
                    self.stdout.write(
                        "  - {}: {}".format(
                            item.get("word"), item.get("reason", "ready")
                        )
                    )
        if options["apply"] and report["conflict"]:
            raise CommandError(
                "Import aborted; {} conflict(s) found and no entries were written.".format(
                    len(report["conflict"])
                )
            )
