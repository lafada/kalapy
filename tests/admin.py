#!/usr/bin/env python
import os, sys

# make kalapy namespace avialable
sys.path.append(os.path.abspath(os.path.pardir))

from kalapy import admin
try:
    import settings
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find 'settings.py`. It seems that you are running admin util from outside the project dir.")
    sys.exit(1)

if __name__ == "__main__":
    admin.execute_command(None, settings)

