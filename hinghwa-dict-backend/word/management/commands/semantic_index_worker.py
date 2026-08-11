import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from word.search.worker import SemanticIndexWorker


class Command(BaseCommand):
    help = "Build and continuously refresh the word semantic-search index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process at most one pending revision and exit",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Request a new revision before processing",
        )
        parser.add_argument(
            "--poll-seconds",
            type=float,
            default=settings.SEMANTIC_SEARCH_WORKER_POLL_SECONDS,
        )

    def handle(self, *args, **options):
        worker = SemanticIndexWorker()
        force = options["force"]
        if options["once"]:
            try:
                built = worker.run_once(force=force)
            except Exception as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write("semantic index built" if built else "no rebuild pending")
            return

        backoff = max(options["poll_seconds"], 0.1)
        while True:
            try:
                built = worker.run_once(force=force)
                force = False
                backoff = max(options["poll_seconds"], 0.1)
                if not built:
                    time.sleep(backoff)
            except KeyboardInterrupt:
                return
            except Exception:
                time.sleep(backoff)
                backoff = min(
                    backoff * 2,
                    settings.SEMANTIC_SEARCH_WORKER_MAX_BACKOFF_SECONDS,
                )
