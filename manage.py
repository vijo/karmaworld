#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Making sure we can import each app
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(PROJECT_ROOT, 'karmaworld/apps'))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "karmaworld.settings.vmdev")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
