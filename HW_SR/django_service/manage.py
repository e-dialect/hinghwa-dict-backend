#!/usr/bin/env python
"""Django 入口脚本。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_service.config.settings")

from django.core.management import execute_from_command_line


def main() -> None:
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()