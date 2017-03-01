from django import template
from django.forms.widgets import Select
from django.utils.http import urlquote
from pjwidgets.core import get_widget_list

register = template.Library()

@register.simple_tag(takes_context=True)
def render_widget(context, widget, *args, **kwargs):
    return widget.get_widget_instance().render_widget(context, *args, **kwargs)

@register.simple_tag()
def widget_selector(name='widget_name', value=None):
    return Select(choices=get_widget_list()).render(name, value)

@register.filter()
def add_float(value, arg):
    return float(value) + float(arg)

@register.simple_tag(takes_context=True)
def absolute_uri(context, url, quote=False):
    res = context['request'].build_absolute_uri(url)
    return urlquote(res) if quote else res