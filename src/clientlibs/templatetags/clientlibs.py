import re
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.conf import settings

lib_dict = __import__('clientlibs.libdefs').libdefs.lib_dict

register = template.Library()

@register.simple_tag
def clientlib(libname, escape_tags=False):
    
    def get_file_url(filedef):
        use_cdn = filedef['force_cdn'] if 'force_cdn' in filedef else getattr(settings,'USE_CDN',True)
        return filedef['remote'] if use_cdn else (settings.STATIC_URL + filedef['local'])
    
    res = []
    library = lib_dict.get(libname,None)
    if not library:
        return format_html('<!-- Library {} not found -->',libname)
    for cssfile in library['files'].get('css',[]):
        res.append(format_html('<link rel="stylesheet" type="text/css" href="{}" />', get_file_url(cssfile)))
    for jsfile in library['files'].get('js',[]):
        res.append(format_html('<script src="{}"> </script>', get_file_url(jsfile)))
    htmlres = ''.join(res)
    if escape_tags:
        # escape_tags makes it safe for conditional loading using document.write()
        htmlres = re.sub('([<>"\'])',r'\\\1',htmlres)
    return mark_safe(htmlres)
    