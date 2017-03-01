from __future__ import unicode_literals

import re
import json
from datetime import timedelta
from django.db import models
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.html import mark_safe
from importlib import import_module
from pjapp.models import Activity, RecordedStep, Project
from ckeditor_uploader.fields import RichTextUploadingField
from pjwidgets.oembed import get_oembed

@python_2_unicode_compatible
class ActivityWidget(models.Model):
    activity = models.ForeignKey(Activity, related_name='widgets', db_index=True, null=False, blank=False)
    title = models.CharField(max_length=200, blank=True, default='')
    widget_name = models.CharField(max_length=200, db_index=True)
    widget_verbose_name = models.CharField(max_length=200, blank=True)
    position_index = models.PositiveSmallIntegerField(db_index=True)
    
    def save(self, *args, **kwargs):
        if self.position_index is None:
            self.position_index = self.activity.widgets.count()
        self.widget_verbose_name = self.get_widget_class().verbose_name
        return super(ActivityWidget, self).save(*args, **kwargs)
    
    def get_widget_class(self):
        module_name, widget_name = self.widget_name.rsplit('.',1)
        return getattr(import_module(module_name), widget_name)
    
    def get_widget_instance(self):
        return (self.get_widget_class())(model = self)
    
    def swap_positions(self, other_widget):
        new_index = other_widget.position_index
        other_widget.position_index = self.position_index
        self.position_index = new_index
        other_widget.save()
        self.save()
    
    def move_up(self):
        widgets_before = self.activity.widgets.filter(position_index__lt=self.position_index)
        if widgets_before.count():
            self.swap_positions(widgets_before.last())
    
    def move_down(self):
        widgets_after = self.activity.widgets.filter(position_index__gt=self.position_index)
        if widgets_after.count():
            self.swap_positions(widgets_after.last())

    def __str__(self):
        return '%s (%s)'%(self.title or '<Untitled widget>', self.widget_verbose_name)
    
    class Meta:
        ordering = ['position_index']

@python_2_unicode_compatible
class BaseWidgetModel(models.Model):
    widget = models.OneToOneField(
        ActivityWidget,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    _title = None
    
    @property
    def title(self):
        if self._title is None:
            if (self.widget and self.pk):
                self._title = self.widget.title
            else:
                self._title = ''
        return self._title
    
    @title.setter
    def title(self, value):
        self._title = value
    
    def save(self, *args, **kwargs):
        super(BaseWidgetModel, self).save(*args, **kwargs)
        if self._title is not None and self._title != self.widget.title:
            self.widget.title = self._title
            self.widget.save()
    
    def __str__(self):
        return 'Extra fields for %s'%(self.widget)
    
    class Meta:
        abstract = True

# MAP WIDGET

class Map(BaseWidgetModel):
    zoom_level = models.IntegerField(default=5, validators=[MinValueValidator(0), MaxValueValidator(18)])
    centre_latitude = models.DecimalField(default=53.0, max_digits=7, decimal_places=5, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    centre_longitude = models.DecimalField(default=-1.0, max_digits=8, decimal_places=5, validators=[MinValueValidator(-180), MaxValueValidator(180)])

@python_2_unicode_compatible
class MapLocation(models.Model):
    COLOUR_CHOICES = ['blue', 'brown', 'cyan', 'green', 'grey', 'orange', 'purple', 'red', 'yellow' ]
    CHOICE_TUPLE = tuple((c,)*2 for c in COLOUR_CHOICES)
    map = models.ForeignKey(Map, related_name='locations', db_index=True, null=False, blank=False)
    colour = models.CharField(max_length=15, choices=CHOICE_TUPLE, default='blue')
    label = models.CharField(max_length=200, db_index=True)
    link_url = models.URLField(max_length=200, blank=True, default='')
    latitude = models.DecimalField(max_digits=7, decimal_places=5, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=8, decimal_places=5, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    
    class Meta:
        ordering = ['label']
    
    def __str__(self):
        return '%s on map "%s"'%(self.label, self.map.widget)

# END MAP WIDGET

# TIME LIMIT WIDGET

class TimeLimit(BaseWidgetModel):
    text_when_early = RichTextUploadingField(blank=True, default='')
    text_when_on_time = RichTextUploadingField(blank=True, default='')
    text_when_late = RichTextUploadingField(blank=True, default='')
    minimum_time = models.DateTimeField(null=True, blank=True)
    maximum_time = models.DateTimeField(null=True, blank=True)

# END TIME LIMIT WIDGET

# CHECK LIST WIDGET

class CheckList(BaseWidgetModel):
    contents = models.TextField()
    allow_custom_items = models.BooleanField(default=False)
    
    def get_tag_list(self):
        return json.loads(self.contents) if self.contents else []
    
    def set_tag_list(self, tag_list):
        self.contents = json.dumps(tag_list)

@python_2_unicode_compatible
class CheckListInstance(models.Model):
    checklist = models.ForeignKey(CheckList, related_name='instances', db_index=True, null=False, blank=False)
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    recordedstep = models.ForeignKey(RecordedStep, db_index=True, null=True, blank=True)
    contents = models.TextField()
    
    def get_tag_list(self):
        return json.loads(self.contents) if self.contents else []
    
    def set_tag_list(self, tag_list):
        self.contents = json.dumps(tag_list)
    
    def __str__(self):
        return 'Instance of %s for %s'%(self.checklist.widget, self.recordedstep if self.recordedstep else self.user)

# END CHECK LIST WIDGET

# OEMBED WIDGET

@python_2_unicode_compatible
class OEmbedHtml(models.Model):
    title = models.CharField(max_length=200, blank=True, default='')
    provider_name = models.CharField(max_length=200, blank=True, default='')
    url = models.URLField(max_length=200, db_index=True, blank=False, null=False, unique=True)
    last_updated = models.DateTimeField(auto_now=True)
    embed_html = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'OEmbed HTML source'
    
    def get_embed_html(self):
        if self.url and ((not self.embed_html) or (now() - self.last_updated > timedelta(days=30))):
            embed_data = get_oembed(self.url)
            self.embed_html = embed_data.get('html','')
            self.title = embed_data.get('title','')
            self.provider_name = embed_data.get('provider_name','')
            self.save()
        return mark_safe(self.embed_html)
    
    def __str__(self):
        return self.url
    
class OEmbed(BaseWidgetModel):
    url = models.URLField(max_length=200, db_index=True, blank=False, null=False)
    
    class Meta:
        verbose_name = 'OEmbed'
        
    def get_oembedhtml(self):
        if not re.match('^https?://', self.url):
            return None
        oeh, created = OEmbedHtml.objects.get_or_create(url=self.url)
        return oeh
    
    def get_embed_html(self):
        if not re.match('^https?://', self.url):
            return ''
        return self.get_oembedhtml().get_embed_html()

# END OEMBED WIDGET

# RICHTEXTBLOCK WIDGET

class RichText(BaseWidgetModel):
    contents = RichTextUploadingField(blank=False)

# END RICHTEXTBLOCK WIDGET

# SCANCODES WIDGET

@python_2_unicode_compatible
class CodeContent(models.Model):
    title = models.CharField(max_length=200, blank=False)
    project = models.ForeignKey(Project, db_index=True, null=False, blank=False)
    artcode = models.CharField(max_length=200, blank=True, default='')
    contents = RichTextUploadingField(blank=True, default='')
    
    class Meta:
        verbose_name = 'QR Code/Artcode content'
    
    def get_absolute_url(self):
        return reverse(
            'pjwidgets:codecallback',
            kwargs={'codecontent_id': self.id},
        )
    
    def __str__(self):
        return '%s: %s'%(self.artcode, self.title)
    
class ScanQR(BaseWidgetModel):
    text_before_scanning = RichTextUploadingField(blank=True, default='')
    use_artcodes = models.BooleanField(default=False, blank=True)
    active_codes = models.ManyToManyField(CodeContent)
    
    class Meta:
        verbose_name = 'QR Code/Artcode in activity'
        verbose_name_plural = 'QR Code/Artcode in activities'

@python_2_unicode_compatible
class ScanQRInstance(models.Model):
    scanqr = models.ForeignKey(ScanQR, related_name='instances', db_index=True, null=False, blank=False)
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    recordedstep = models.ForeignKey(RecordedStep, db_index=True, null=True, blank=True)
    code = models.ForeignKey(CodeContent, db_index=True, null=True, blank=True, default=None)
    
    class Meta:
        verbose_name = 'QR Code/Artcode in activity instance'
    
    def __str__(self):
        return 'Instance of %s for %s'%(self.scanqr.widget, self.recordedstep if self.recordedstep else self.user)

# END SCANCODE WIDGET

# START LOCATION WIDGET

class Location(BaseWidgetModel):
    text_when_not_on_location = RichTextUploadingField(blank=True, default='')
    text_when_on_location = RichTextUploadingField(blank=True, default='')
    show_map = models.BooleanField(default=True, blank=True)
    latitude = models.DecimalField(max_digits=7, decimal_places=5, validators=[MinValueValidator(-90), MaxValueValidator(90)], default=52.95333)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, validators=[MinValueValidator(-180), MaxValueValidator(180)], default=-1.15028)
    maximum_distance = models.PositiveIntegerField(validators=[MinValueValidator(10)], default=10, help_text='Distance to trigger content, in metres', verbose_name='Maximum distance')
    