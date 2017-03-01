from __future__ import unicode_literals

import inspect
from importlib import import_module
from django.apps import apps
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string

class BaseWidget(object):
    
    verbose_name = ''
    widget_template_name = None
    editor_template_name = None
    model = None
        
    class Meta:
        pass
    
    def get_model_class(self):
        return apps.get_model(
            app_label = 'pjwidgets',
            model_name = 'ActivityWidget'
        )
    
    def __init__(self, *args, **kwargs):
        if 'model' in kwargs:
            self.model = kwargs['model']
        if 'pk' in kwargs:
            self.model = get_object_or_404(
                self.get_model_class(),
                pk = kwargs['pk'],
            )
    
    def get_widget_context(self, parent_context, *args, **kwargs):
        return {
            'widget': self.model
        }
    
    def render_widget(self, parent_context, *args, **kwargs):
        context = self.get_widget_context(parent_context, *args, **kwargs)
        return render_to_string(self.widget_template_name, context)
    
    def get_editor_context(self, request, *args, **kwargs):
        return {
            'widget': self.model
        }
    
    def render_editor(self, request, *args, **kwargs):
        context = self.get_editor_context(request, *args, **kwargs)
        if context.get('redirect_to_activity', False):
            return redirect('pjapp:author:explore_activity',pk=self.model.activity_id)
        return render(request, self.editor_template_name, context)

class WidgetWithForm(BaseWidget):
    
    extra_model = None
    form = None
    
    def get_editor_context(self, request, *args, **kwargs):
        extra_model_instance, created = self.extra_model.objects.get_or_create(
            widget = self.model,
        )
        context = {
            'widget': self.model,
        }
        if request.method == 'POST':
            form_instance = self.form(
                request.POST,
                instance = extra_model_instance,
            )
            if form_instance.is_valid():
                form_instance.save()
                context['redirect_to_activity'] = True
        else:
            form_instance = self.form(
                instance = extra_model_instance,
            )
        context['form'] = form_instance
        return context

def get_widget_list():
    widget_list = []
    for module_name in settings.MODULES_PROVIDING_WIDGETS:
        mod = import_module(module_name)
        members = inspect.getmembers(mod)
        members = [ cls for cls_name, cls in members if inspect.isclass(cls) ]
        members = [ cls for cls in members if cls.__module__ == module_name ]
        widgets = [ cls for cls in members if BaseWidget in inspect.getmro(cls) ]
        widget_list += [('%s.%s'%(module_name, cls.__name__), cls.verbose_name) for cls in widgets]
    widget_list.sort(key=lambda w: w[1])
    return widget_list
