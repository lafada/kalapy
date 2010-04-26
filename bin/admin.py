#!/usr/bin/env python

import sys
from os.path import exists, dirname, abspath

# if running from the rapido-project's workspace dir
if (exists("rapido/admin/__init__.py")):
    sys.path.insert(0, dirname(dirname(abspath(__file__))))

from rapido import admin

if __name__ == "__main__":
    admin.execute()

