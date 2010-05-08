#!/usr/bin/env python

import unittest
import os, sys, traceback

from optparse import OptionParser

def get_packages():
    for d in os.listdir('.'):
        if os.path.isdir(d) and os.path.exists(os.path.join(d, 'tests.py')):
            yield d

def run_rapido_tests(*args):
    
    try:
        import settings as settings_module
    except:
        raise Exception('runtests.py should be run from tests dir')

    from rapido.conf import settings
    settings.update(settings_module)
    
    from rapido import db
    from rapido.test import run_tests

    # load all models
    db.get_models()

    args = args or list(get_packages())

    run_tests(args, 2)


if __name__ == "__main__":

    usage = """%prog [options] [name [name [name [...]]]]"""
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()

    # make rapido namespace avialable
    sys.path.append(os.path.abspath(os.path.pardir))

    run_rapido_tests(*args)

