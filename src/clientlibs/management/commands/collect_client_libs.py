import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template import engines
from django.template.loader import get_template
from clientlibs.libdefs import lib_dict
from clientlibs.templatetags.clientlibs import clientlib
try:
    from urllib import urlretrieve
except:
    from urllib.request import urlretrieve

class Command(BaseCommand):
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help='Overwrite existing files'
        )
    
    def handle(self, *args, **options):
        
        print("Processing all templates")
        
        used_libs = []
        
        def parse_node(node):
            if hasattr(node, 'nodelist'):
                for childnode in node.nodelist:
                    parse_node(childnode)
            if getattr(node, 'func', None) == clientlib:
                libname = node.args[0].var
                if not libname in used_libs:
                    used_libs.append(libname)
        
        tmplfiles = []
        for e in engines.all():
            for tmpldir in getattr(e, 'template_dirs', []):
                for dirpath, dirnames, filenames in os.walk(tmpldir):
                    for filename in filenames:
                        tmplfiles.append(os.path.join(dirpath, filename))
        l = len(tmplfiles)
        for i, filename in enumerate(tmplfiles):
            print("Parsing template %d of %d: %s"%(i,l,filename))
            parse_node(get_template(filename).template)
        
        print('%d libs used: %s'%(len(used_libs),', '.join(used_libs)))
        
        for libname in used_libs:
            libdef = lib_dict[libname]
            print("\nLoading files for %s:" % libname)
            for filetype, filedefs in libdef.get('files',{}).items():
                for filedef in filedefs:
                    if filedef.get('force_cdn', False):
                        print("    Skipping '%s' (will always be served remotely)"%filedef['remote'])
                    else:
                        localfile = os.path.join(settings.STATIC_ROOT, filedef['local'])
                        if os.path.exists(localfile) and not options['overwrite']:
                            print("    '%s' already exists."%filedef['local'])
                        else:
                            localdir = os.path.dirname(localfile)
                            if not os.path.exists(localdir):
                                os.makedirs(localdir)
                            print("    Retrieving '%s'"%filedef['local'])
                            try:
                                urlretrieve(filedef['remote'], localfile)
                            except Exception as e:
                                print("  /!\\ Error %s when retrieving %s"%(e,filedef['remote']))
                