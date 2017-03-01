from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.contrib.admin import register, ModelAdmin
from django.db.models import Count
from django.forms import ModelForm
from django.template.defaultfilters import truncatechars
from django.utils.safestring import mark_safe
from pjapp import models as app_models

# Register your models here.

@register(app_models.Tag)
class TagAdmin(ModelAdmin):
    
    list_display = ('__str__', 'project_count', 'activity_count', 'path_count')
    
    def project_count(self, obj):
        cnt = getattr(obj, 'project_count', 0)
        url = reverse("admin:pjapp_project_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?tags__id__exact=%d">%d</a>'%(url, obj.id, cnt))
    
    def activity_count(self, obj):
        cnt = getattr(obj, 'activity_count', 0)
        url = reverse("admin:pjapp_activity_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?tags__id__exact=%d">%d</a>'%(url, obj.id, cnt))
    
    def path_count(self, obj):
        cnt = getattr(obj, 'path_count', 0)
        url = reverse("admin:pjapp_path_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?tags__id__exact=%d">%d</a>'%(url, obj.id, cnt))

    def get_queryset(self, request):
        return super(TagAdmin, self).get_queryset(request).annotate(
                               project_count = Count('project', distinct=True),
                               activity_count = Count('activity', distinct=True),
                               path_count = Count('path', distinct=True),
                               )

@register(app_models.Project)
class ProjectAdmin(ModelAdmin):
    
    list_display = ('__str__', 'activity_count', 'path_count','creator','date_created','date_updated','tag_list',)
    list_display_links = ('__str__',)
    list_filter = ('creator','date_created','date_updated','tags',)
    readonly_fields = ('activity_count', 'path_count','date_created','date_updated',)
    
    def tag_list(self, obj):
        return ", ".join([t.text for t in obj.tags.all()]) if obj.tags.count() else '-'
    
    def activity_count(self, obj):
        cnt = getattr(obj, 'activity_count', 0)
        url = reverse("admin:pjapp_activity_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?project__id__exact=%d">%d</a>'%(url, obj.id, cnt))
    
    def path_count(self, obj):
        cnt = getattr(obj, 'path_count', 0)
        url = reverse("admin:pjapp_path_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?project__id__exact=%d">%d</a>'%(url, obj.id, cnt))
    
    def get_queryset(self, request):
        return super(ProjectAdmin, self).get_queryset(request).annotate(
                               activity_count = Count('activities', distinct=True),
                               path_count = Count('paths', distinct=True)
                               )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(ProjectAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['creator'].initial = request.user
        return form

@register(app_models.Activity)
class ActivityAdmin(ModelAdmin):
    
    list_display = ('__str__', 'project', 'date_created', 'date_updated', 'tag_list',)
    list_display_links = ('__str__',)
    list_filter = ('project','date_created','date_updated','tags',)
    list_select_related = ('project',)
    readonly_fields = ('date_created','date_updated',)
    
    def tag_list(self, obj):
        return ", ".join([t.text for t in obj.tags.all()]) if obj.tags.count() else '-'

@register(app_models.Path)
class PathAdmin(ModelAdmin):
    
    list_display = ('__str__', 'project', 'link_count', 'activity_count', 'date_created', 'date_updated', 'tag_list')
    list_display_links = ('__str__',)
    list_filter = ('project','date_created','date_updated','tags',)
    list_select_related = ('project',)
    readonly_fields = ('link_count', 'activity_count','date_created','date_updated',)
    
    def tag_list(self, obj):
        return ", ".join([t.text for t in obj.tags.all()]) if obj.tags.count() else '-'
    
    def link_count(self, obj):
        cnt = getattr(obj, 'link_count', 0)
        url = reverse("admin:pjapp_pathlink_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?path__id__exact=%d">%d</a>'%(url, obj.id, cnt))
    
    def activity_count(self, obj):
        activities = obj.get_activities()
        cnt = activities.count()
        url = reverse("admin:pjapp_activity_changelist")
        if not cnt:
            return '-'
        return mark_safe('<a href="%s?id__in=%s">%d</a>'%(
                                                           url,
                                                           ",".join([str(a.id) for a in activities]),
                                                           cnt
                                                           ))
    
    def get_queryset(self, request):
        return super(PathAdmin, self).get_queryset(request).annotate(
                                                                     link_count=Count('links', distinct=True)
                                                                     )

class PathLinkAdminForm(ModelForm):
    class Meta:
        model = app_models.PathLink
        exclude = []
    
    def __init__(self, *args, **kwargs):
        super(PathLinkAdminForm, self).__init__(*args, **kwargs)
        self.fields['from_activity'].empty_label = "Start of trajectory"
        self.fields['to_activity'].empty_label = "End of trajectory"
        
@register(app_models.PathLink)
class PathLinkAdmin(ModelAdmin):
    
    form = PathLinkAdminForm
    list_display = ('pk', 'project', 'path', 'link_from', 'link_to', 'date_created', 'date_updated')
    list_display_links = ('pk',)
    list_filter = ('path__project','path',)
    list_select_related = ('path','from_activity','to_activity',)
    readonly_fields = ('date_created','date_updated',)
    
    def project(self, obj):
        return obj.path.project
    
    def link_from(self, obj):
        return (obj.from_activity if obj.from_activity else "Start of path")
    
    def link_to(self, obj):
        return (obj.to_activity if obj.to_activity else "End of path")

@register(app_models.RecordedPath)
class RecordedPathAdmin(ModelAdmin):
    list_display = ('title', 'path', 'user', 'is_ongoing', 'date_started', 'date_ended',)
    readonly_fields = ('user', 'path', 'date_started', 'date_ended','title',)
    
@register(app_models.RecordedStep)
class RecordedStepAdmin(ModelAdmin):
    list_display = ('get_activity', 'has_custom_activity', 'recorded_path', 'user', 'status', 'date_started', 'date_ended', 'path_index',)
    readonly_fields = ('activity','custom_activity', 'recorded_path', 'user', 'is_canonical', 'status', 'date_started', 'date_ended', 'previous_step', 'next_step', 'path_index',)

    def user(self, obj):
        return obj.recorded_path.user

@register(app_models.Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('comment','user','public','activity','custom_activity','recorded_path','date_created',)
    readonly_fields = ('user','activity','custom_activity','recorded_path','rating','content','image','date_created','public',)
    
    def comment(self, obj):
        return truncatechars(obj.content,40) or '<Empty comment>'
    
@register(app_models.CustomActivity)
class CustomActivityAdmin(ModelAdmin):
    list_display = ('title','user','project',)
    readonly_fields = ('user', 'project', 'title', 'description',)