from __future__ import unicode_literals

import json
import re
from datetime import datetime
from django import forms
from pjwidgets import models as widget_models
from pjapp.forms import TagitWidget, AutocompleteOffForm
from pjwidgets.oembed import providers

class BaseWidgetForm(AutocompleteOffForm):
    
    title = forms.CharField(required=False, max_length=200)
    
    def __init__(self, *args, **kwargs):
        super(BaseWidgetForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['title'].initial = self.instance.title
    
    def save(self, force_insert=False, force_update=False, commit=True):
        instance = super(BaseWidgetForm, self).save(commit=False)
        instance.title = self.cleaned_data['title']
        if commit == True:
            instance.save()
        return instance

class MapForm(BaseWidgetForm):
     
    class Meta:
        model = widget_models.Map
        fields = [ 'title', 'zoom_level', 'centre_latitude', 'centre_longitude' ]
         
class MapLocationForm(AutocompleteOffForm):
    
    class Meta:
        model = widget_models.MapLocation
        fields = [ 'label', 'link_url', 'latitude', 'longitude', 'colour' ]
        widgets = {
            'colour': forms.HiddenInput()
        }

MapLocationFormset = forms.inlineformset_factory(
    widget_models.Map,
    widget_models.MapLocation,
    form = MapLocationForm,
    extra = 1,
)

class TimeLimitForm(BaseWidgetForm):
    
    has_minimum_time = forms.BooleanField(
        required=False,
        label='Minimum time',
    )
    minimum_time_date = forms.DateField(
        required = False,
        label = 'Date',
        input_formats = [ '%d/%m/%Y' ],
        widget=forms.DateInput(
            attrs={
                'class':'date-picker',
                'placeholder': 'dd/mm/yy',
            }
        ),
    )
    minimum_time_time = forms.TimeField(
        required=False,
        label='Time',
        widget=forms.TimeInput(
            attrs={
                'placeholder': 'hh:mm:ss',
            }
        ),
    )
    has_maximum_time = forms.BooleanField(
        required=False,
        label='Maximum time',
    )
    maximum_time_date = forms.DateField(
        required = False,
        label = 'Date',
        input_formats = [ '%d/%m/%Y' ],
        widget=forms.DateInput(
            attrs={
                'class':'date-picker',
                'placeholder': 'dd/mm/yy',
            }
        ),
    )
    maximum_time_time = forms.TimeField(
        required=False,
        label='Time',
        widget=forms.TimeInput(
            attrs={
                'placeholder': 'hh:mm:ss',
            }
        ),
    )
    
    def __init__(self, *args, **kwargs):
        super(TimeLimitForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.minimum_time:
                self.fields['has_minimum_time'].initial = True
                self.fields['minimum_time_date'].initial = self.instance.minimum_time.date()
                self.fields['minimum_time_time'].initial = self.instance.minimum_time.time()
            if self.instance.maximum_time:
                self.fields['has_maximum_time'].initial = True
                self.fields['maximum_time_date'].initial = self.instance.maximum_time.date()
                self.fields['maximum_time_time'].initial = self.instance.maximum_time.time()
    
    def clean(self):
        cleaned_data = super(TimeLimitForm, self).clean()
        if cleaned_data['has_minimum_time'] == True:
            if not cleaned_data.get('minimum_time_date', None):
                raise forms.ValidationError("You must provide a valid minimum date")
            if not cleaned_data.get('minimum_time_time', None):
                raise forms.ValidationError("You must provide a valid minimum time")
        if cleaned_data['has_maximum_time'] == True:
            if not cleaned_data.get('maximum_time_date', None):
                raise forms.ValidationError("You must provide a valid maximum date")
            if not cleaned_data.get('maximum_time_time', None):
                raise forms.ValidationError("You must provide a valid maximum time")
        if not cleaned_data['has_maximum_time'] and not cleaned_data['has_minimum_time']: 
            raise forms.ValidationError("You must provide at least either a minimum or maximum time")
        if cleaned_data['has_maximum_time'] and cleaned_data['has_minimum_time']:
            minimum_time = datetime.combine(
                self.cleaned_data['minimum_time_date'],
                self.cleaned_data['minimum_time_time'],
            )
            maximum_time = datetime.combine(
                self.cleaned_data['maximum_time_date'],
                self.cleaned_data['maximum_time_time'],
            )
            if maximum_time < minimum_time:
                raise forms.ValidationError("Minimum time must be before maximum time")
        return cleaned_data
    
    def save(self, force_insert=False, force_update=False, commit=True):
        instance = super(TimeLimitForm, self).save(commit=False)
        if self.cleaned_data['has_minimum_time'] == True:
            instance.minimum_time = datetime.combine(
                self.cleaned_data['minimum_time_date'],
                self.cleaned_data['minimum_time_time'],
            )
        else:
            instance.minimum_time = None
            instance.text_when_early = ''
        if self.cleaned_data['has_maximum_time'] == True:
            instance.maximum_time = datetime.combine(
                self.cleaned_data['maximum_time_date'],
                self.cleaned_data['maximum_time_time'],
            )
        else:
            instance.maximum_time = None
            instance.text_when_late = ''
        if commit:
            instance.save()
        return instance
    
    class Meta:
        model = widget_models.TimeLimit
        fields = [
            'title','has_minimum_time','minimum_time_date','minimum_time_time','text_when_early',
            'text_when_on_time','has_maximum_time','maximum_time_date','maximum_time_time','text_when_late',
        ]

class CheckListForm(BaseWidgetForm):
    
    allow_custom_items = forms.BooleanField(required=False)
    
    class Meta:
        model = widget_models.CheckList
        fields = [ 'title', 'contents', 'allow_custom_items' ]
        widgets = {
            'contents': forms.HiddenInput()
        }

class OEmbedForm(BaseWidgetForm):
        
    class Meta:
        model = widget_models.OEmbed
        fields = [ 'title', 'url' ]
        widgets = {
            'url': forms.TextInput(attrs={
                 'placeholder': 'Type the URL you wish to embed',
                 'size': 40,
            }),
            'title': forms.HiddenInput(),
        }

class RichTextForm(BaseWidgetForm):
       
    class Meta:
        model = widget_models.RichText
        fields = [ 'title', 'contents' ]

class ScanQRForm(BaseWidgetForm):
       
    class Meta:
        model = widget_models.ScanQR
        fields = [ 'title', 'text_before_scanning', 'use_artcodes' ]

class EditCodeContentForm(AutocompleteOffForm):
    
    def clean_artcode(self):
        data = self.cleaned_data['artcode']
        if data and not re.match(r'^(?:[1-9]\:)+[1-9]$',data):
            raise forms.ValidationError('"%s" is not a valid artcode'%data)
        return data
    
    class Meta:
        model = widget_models.CodeContent
        fields = ['title', 'contents', 'artcode']

class LocationWidgetForm(BaseWidgetForm):
     
    class Meta:
        model = widget_models.Location
        fields = [ 'title', 'show_map', 'maximum_distance', 'latitude', 'longitude', 'text_when_not_on_location', 'text_when_on_location', ]