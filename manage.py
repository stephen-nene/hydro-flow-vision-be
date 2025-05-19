#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Django's command-line utility for administrative tasks."""

import os
import sys

MIN_PYTHON = (3, 7)

def main():
    """Run administrative tasks."""
    if sys.version_info < MIN_PYTHON:
        sys.stderr.write(
            f"Error: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher is required.\n"
        )
        sys.exit(1)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it's installed and "
            "available on your PYTHONPATH environment variable. Did you "
            "forget to activate a virtual environment?\n"
            f"Original error: {exc}"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()