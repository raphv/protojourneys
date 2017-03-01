from __future__ import unicode_literals

import json
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from pjapp.models import Project, Activity, Path, CustomActivity

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).count():
            raise forms.ValidationError("This email address is already registered.")

class CustomLoginForm(forms.Form):
    email_or_username = forms.CharField(widget=forms.TextInput(), required=True, label="Username or email")
    password = forms.CharField(widget=forms.PasswordInput(), required=True, label="Password" )
    
    def clean(self):
        cleaned_data = super(CustomLoginForm, self).clean()
        email_or_username = cleaned_data.get("email_or_username")
        try:
            user = User.objects.get(username=email_or_username)
        except:
            try:
                user = User.objects.get(email=email_or_username)
            except:
                raise forms.ValidationError("User unknown")
        cleaned_data["user"] = user
        if not user.check_password(cleaned_data.get("password")):
            raise forms.ValidationError("Incorrect password")
        return cleaned_data

class AutocompleteOffForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super(AutocompleteOffForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['autocomplete'] = 'off'

class TagitWidget(forms.TextInput):
    class Media:
        css = {
               'all': (
                       'lib/jquery-ui.min.css',
                       'lib/jquery.tagit.css',
                       )
               }
        js = (
              'lib/jquery.min.js',
              'lib/jquery-ui.min.js',
              'lib/tag-it.min.js',
              )
    
    def render(self, name, value, attrs=None):
        base_html = super(TagitWidget, self).render(name, value, attrs)
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        js = '$(function(){var $el = $("#%s"), config = JSON.parse($el.attr("tagit-config")||"{}"); $el.tagit(config);});'%attrs['id']
        return mark_safe('%s<script>%s</script>'%(base_html, js))
    
class TagListForm(AutocompleteOffForm):

    tag_list = forms.CharField(widget=TagitWidget, required=False)
    
    def __init__(self, *args, **kwargs):
        super(TagListForm, self).__init__(*args, **kwargs)
        if self.instance:
            self.fields['tag_list'].initial = self.instance.flat_tag_list
        self.fields['tag_list'].widget.attrs = {
            'tagit-config': json.dumps({
                'autocomplete': {
                    'source': reverse('pjapp:author:tag_autocomplete')
                }
            }),
        }
    
    def save(self, force_insert=False, force_update=False, commit=True):
        instance = super(TagListForm, self).save(commit=False)
        instance.flat_tag_list = self.cleaned_data['tag_list']
        if commit:
            instance.save()
        return instance
    
class EditProjectForm(TagListForm):
    
    class Meta:
        model = Project
        fields = ['title', 'description', 'tag_list', 'annotations']

class EditActivityForm(TagListForm):
    
    class Meta:
        model = Activity
        fields = ['title', 'description', 'tag_list', 'annotations']

class EditPathForm(TagListForm):
    
    class Meta:
        model = Path
        fields = ['title', 'description', 'listed_publicly', 'tag_list', 'annotations']

class CustomActivityForm(forms.ModelForm):
    
    class Meta:
        model = CustomActivity
        fields = ['title', 'description']
