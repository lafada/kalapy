"""
kalapy.admin.commands.project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements `startproject` and `startpackage` commands to
start a new project or an application package.

:copyright: (c) 2010 Amit Mendapara.
:license: BSD, see LINCESE for more details.
"""
import os, sys, re, shutil, string

from kalapy.admin import Command


JUNK_FILE = re.compile('^(.*?)(\.swp|\.pyc|\.pyo|\~)$')

def copy_helper(arg, path, files):

    base, name, verbose = arg

    dest = os.path.relpath(path, base)
    dest = os.path.join(name, dest) if dest != '.' else name

    if verbose:
        sys.stdout.write('Creating dir %s\n' % dest)
    try:
        os.mkdir(dest)
    except OSError, e:
        raise CommandError(e)

    for f in files:

        if JUNK_FILE.match(f):
            continue

        n = os.path.join(dest, f)
        f = os.path.join(path, f)

        if verbose:
            sys.stdout.write('Creating file %s\n' % n)

        f_old = open(f, 'r')
        f_new = open(n, 'w')

        content = string.Template(f_old.read()).safe_substitute(name=name)

        f_new.write(content)

        f_old.close()
        f_new.close()

        try:
            shutil.copymode(f, n)
        except OSError:
            pass


def copy_template(template, name, verbose=False):

    pat = re.compile('^[_a-zA-Z]\w*$')

    if not pat.search(name):
        raise CommandError("Invalid name '%s'" % name)

    try:
        __import__(name)
        raise CommandError('name conflicts with existing python module.')
    except ImportError:
        pass

    basedir = os.path.dirname(os.path.dirname(__file__))
    basedir = os.path.join(basedir, template)

    os.path.walk(basedir, copy_helper, [basedir, name, verbose])


class StartProject(Command):
    """start a new project
    """
    name = "startproject"
    usage = "%name <name>"

    scope = None

    def execute(self, options, args):
        try:
            name = args[0]
        except:
            self.print_help()

        copy_template('project_template', name=name, verbose=options.verbose)


class StartApp(Command):
    """start a new package
    """
    name = "startpackage"
    usage = "%name <name>"

    def execute(self, options, args):
        try:
            name = args[0]
        except:
            self.print_help()

        copy_template('package_template', name=name, verbose=options.verbose)

        for d in ('static', 'templates',):
            os.mkdir('%s/%s' % (name, d))

