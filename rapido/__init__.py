import os, site

MOX_LIBDIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lib')
if os.path.isdir(MOX_LIBDIR):
    site.addsitedir(MOX_LIBDIR)

del MOX_LIBDIR
del site
del os

