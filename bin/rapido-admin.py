#!/usr/bin/env python
from rapido import admin
try:
    import settings
except ImportError:
    settings = None
    
if __name__ == "__main__":
    admin.execute_command(None, settings)

