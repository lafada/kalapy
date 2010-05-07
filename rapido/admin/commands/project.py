import os, sys, re, shutil, string

from rapido.admin import BaseCommand, CommandError
from rapido.utils.implib import import_module


def copy_helper(arg, path, files):
    
    base, name = arg
    
    dest = os.path.relpath(path, base)
    dest = os.path.join(name, dest) if dest != '.' else name
    
    sys.stdout.write('Creating dir %s\n' % dest)
    try:
        os.mkdir(dest)
    except OSError, e:
        raise CommandError(e)
        
    for f in files:
        
        if not f.endswith('.py'):
            continue
         
        n = os.path.join(dest, f)
        f = os.path.join(path, f)
        
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
        
 
def copy_template(template, name):
    
    pat = re.compile('^[_a-zA-Z]\w*$')
    
    if not pat.search(name):
        raise CommandError("Invalid name '%s'" % name)
    
    try:
        import_module(name)
        raise CommandError('name conflicts with existing python module.')
    except ImportError:
        pass
    
    basedir = os.path.dirname(os.path.dirname(__file__))
    basedir = os.path.join(basedir, template)
    
    os.path.walk(basedir, copy_helper, [basedir, name])


class StartProject(BaseCommand):

    name = "startproject"
    help = "start a new project"
    args = "<name>"
    scope = "project"
    
    def execute(self, *args, **options):
        try:
            name = args[0]
        except:
            self.print_help()
        
        copy_template('project_template', name=name)
        

class StartApp(BaseCommand):
    
    name = "startpackage"
    help = "start a new package"
    args = "<name>"
    scope = "package"
    
    def execute(self, *args, **options):
        try:
            name = args[0]
        except:
            self.print_help()
            
        copy_template('package_template', name=name)
