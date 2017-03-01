import json
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import timezone
from pjwidgets.core import BaseWidget, WidgetWithForm
from pjwidgets import models as widget_models
from pjwidgets import forms as widget_forms

class MapWidget(BaseWidget):
    
    verbose_name = 'Map with multiple locations'
    widget_template_name = 'pjwidgets/render/map.html'
    editor_template_name = 'pjwidgets/edit/map.html'
    
    def get_widget_context(self, parent_context, *args, **kwargs):
        map = self.model.map
        json_data = {
            'zoom': map.zoom_level,
            'centre': [str(map.centre_latitude), str(map.centre_longitude)],
            'locations': [{
                'position': [str(l.latitude), str(l.longitude)],
                'label': l.label,
                'url': l.link_url,
                'colour': l.colour,
            } for l in map.locations.all()]
        }
        context = {
            'widget': self.model,
            'map_json': json.dumps(json_data),
            'map': map,
        }
        return context
    
    def get_editor_context(self, request, *args, **kwargs):
        map, created = widget_models.Map.objects.get_or_create(
            widget = self.model,
        )
        formarg = request.POST or None
        form = widget_forms.MapForm(formarg, instance=map)
        formset = widget_forms.MapLocationFormset(formarg, instance=map)
        if form.is_valid():
            form.save()
            form = widget_forms.MapForm(instance=map)
        if formset.is_valid():
            formset.save()
            formset = widget_forms.MapLocationFormset(instance=map)
        
        context = {
            'map': map,
            'form': form,
            'formset': formset,
        }
        
        json_data = {
            'api_key': settings.GOOGLE_API_KEY,
            'zoom': map.zoom_level,
            'centre': [str(map.centre_latitude), str(map.centre_longitude)],
            'locations': [{
                'id': l.id,
                'position': [str(l.latitude), str(l.longitude)],
                'label': l.label,
                'url': l.link_url,
                'colour': l.colour,
             } for l in map.locations.all()]
        }
        context['map_json'] = json.dumps(json_data)
        context['COLOUR_CHOICES'] = widget_models.MapLocation.COLOUR_CHOICES
        return context

class TimeLimitWidget(WidgetWithForm):
    
    verbose_name = 'Time triggered content'
    widget_template_name = 'pjwidgets/render/timelimit.html'
    editor_template_name = 'pjwidgets/edit/timelimit.html'
    extra_model = widget_models.TimeLimit
    form = widget_forms.TimeLimitForm
    
    def get_widget_context(self, parent_context, *args, **kwargs):
        timelimit = self.model.timelimit
        now = timezone.now()
        early = (timelimit.minimum_time and timelimit.minimum_time > now)
        late = (timelimit.maximum_time and timelimit.maximum_time < now)
        context = {
            'now': now,
            'timelimit': timelimit,
            'early': early,
            'late': late,
            'available': not early and not late,
        }
        return context

class CheckListWidget(WidgetWithForm):
    
    verbose_name = 'Checklist'
    widget_template_name = 'pjwidgets/render/checklist.html'
    editor_template_name = 'pjwidgets/edit/checklist.html'
    extra_model = widget_models.CheckList
    form = widget_forms.CheckListForm
    
    def get_widget_context(self, parent_context, *args, **kwargs):
        checklist = self.model.checklist
        user = parent_context['request'].user
        getkwargs = {
            'checklist': checklist,
            'user': user,
        }
        if 'step' in parent_context:
            getkwargs['recordedstep'] = parent_context['step']
        clinstance, created = widget_models.CheckListInstance.objects.get_or_create(**getkwargs)
        base_list = checklist.get_tag_list()
        user_list = clinstance.get_tag_list()
        context = {
            'checklist': checklist,
            'checklist_instance': clinstance,
            'base_items': [{
                'text': item,
                'checked': (item in user_list),
            } for item in base_list],
            'csrf_token': parent_context['csrf_token']
        }
        if checklist.allow_custom_items:
            context['allow_custom_items'] = True
            context['user_items'] = [item for item in user_list if item not in base_list]
        return context

class OEmbedWidget(WidgetWithForm):
    
    verbose_name = 'URL embed'
    widget_template_name = 'pjwidgets/render/oembed.html'
    editor_template_name = 'pjwidgets/edit/oembed.html'
    extra_model = widget_models.OEmbed
    form = widget_forms.OEmbedForm
    
    def get_editor_context(self, request, *args, **kwargs):
        context = super(OEmbedWidget, self).get_editor_context(request, *args, **kwargs)
        context['oembedhtml'] = self.model.oembed.get_oembedhtml()
        if context['oembedhtml']:
            context['oembedhtml'].get_embed_html()
        return context

class RichTextWidget(WidgetWithForm):
    
    verbose_name = 'Text Block'
    widget_template_name = 'pjwidgets/render/richtext.html'
    editor_template_name = 'pjwidgets/edit/richtext.html'
    extra_model = widget_models.RichText
    form = widget_forms.RichTextForm


class ScanQRWidget(WidgetWithForm):
    
    verbose_name = 'Code [QR/Artcode] triggered content'
    widget_template_name = 'pjwidgets/render/scanqr.html'
    editor_template_name = 'pjwidgets/edit/scanqr.html'
    extra_model = widget_models.ScanQR
    form = widget_forms.ScanQRForm
    
    def get_widget_context(self, parent_context, *args, **kwargs):
        scanqr = self.model.scanqr
        request = parent_context['request']
        user = request.user
        getkwargs = {
            'scanqr': scanqr,
            'user': user,
        }
        if 'step' in parent_context:
            getkwargs['recordedstep'] = parent_context['step']
        codeinstance, created = widget_models.ScanQRInstance.objects.get_or_create(**getkwargs)
        context = {
            'widget': self.model,
            'scanqr_instance': codeinstance,
        }
        if scanqr.use_artcodes:
            ua_string = request.META.get('HTTP_USER_AGENT', '')
            is_android = ('Android' in ua_string)
            is_ios = ('iPhone' in ua_string or 'iPad' in ua_string or 'iPod' in ua_string)
            if is_ios != is_android: # Logical XOR that filters out Windows Phones!
                context['show_app'] = True
                context['is_android'] = is_android
        return context
    
    def get_editor_context(self, request, *args, **kwargs):
        context = super(ScanQRWidget, self).get_editor_context(request, *args, **kwargs)
        active_codes = self.model.scanqr.active_codes.all()
        context['active_codes'] = active_codes
        context['inactive_codes'] = widget_models.CodeContent.objects.filter(
            project = self.model.activity.project
        ).exclude(
            id__in = active_codes.values_list('id')
        )
        return context

class LocationWidget(WidgetWithForm):
    
    verbose_name = 'Location triggered content'
    widget_template_name = 'pjwidgets/render/location.html'
    editor_template_name = 'pjwidgets/edit/location.html'
    extra_model = widget_models.Location
    form = widget_forms.LocationWidgetForm     
