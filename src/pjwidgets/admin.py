from django.contrib import admin
from pjwidgets import models as widget_models
from django.forms import ModelForm, ChoiceField
from pjwidgets.core import get_widget_list

class ActivityWidgetAdminForm(ModelForm):
    
    class Meta:
        model = widget_models.ActivityWidget
        exclude = ['widget_verbose_name']
        
    def __init__(self, *args, **kwargs):
        super(ActivityWidgetAdminForm, self).__init__(*args, **kwargs)
        self.fields['widget_name'] = ChoiceField(choices=get_widget_list())
        self.fields['position_index'].required = False
    
@admin.register(widget_models.ActivityWidget)
class ActivityWidgetAdmin(admin.ModelAdmin):
    form = ActivityWidgetAdminForm

admin.site.register(widget_models.Map)
admin.site.register(widget_models.MapLocation)

admin.site.register(widget_models.TimeLimit)

admin.site.register(widget_models.CheckList)
admin.site.register(widget_models.CheckListInstance)

admin.site.register(widget_models.OEmbed)
admin.site.register(widget_models.OEmbedHtml)

admin.site.register(widget_models.RichText)

admin.site.register(widget_models.ScanQR)
admin.site.register(widget_models.ScanQRInstance)
admin.site.register(widget_models.CodeContent)

admin.site.register(widget_models.Location)
