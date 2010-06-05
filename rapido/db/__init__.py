"""
rapido.db
~~~~~~~~~

This module implements the DAL API, an unique database abstraction layer 
inspired of OpenERP and Django ORM.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LICENSE for more details.
"""
from rapido.db.engines import DatabaseError, IntegrityError, commit, rollback

from fields import *
from reference import *
from model import *
from query import *
from helpers import *

# remove module references to hide them from direct outside access
map(lambda n: globals().pop(n), ['engines', 'model', 'fields', 'query', 'reference', 'helpers'])

