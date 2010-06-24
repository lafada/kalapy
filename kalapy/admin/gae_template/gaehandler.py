#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(PROJECT_DIR, 'lib'))

from wsgiref.handlers import CGIHandler
from kalapy.web import Application
from kalapy.admin import setup_environment

import settings
setup_environment(settings)

def main():
    app = Application()
    CGIHandler().run(app)

if __name__ == "__main__":
    main()

