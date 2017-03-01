from django.contrib.admin import register, ModelAdmin
from django.utils.html import format_html_join
from django.core.urlresolvers import reverse
from consent.models import ConsentItem, UserConsent
from consent.forms import ConsentAdminForm

@register(ConsentItem)
class ConsentAdmin(ModelAdmin):

    form = ConsentAdminForm
    list_display = ('__str__', 'answer_with', 'move_item')
    readonly_fields = ('move_item',)
    
    def answer_with(self, obj):
        return 'Yes' if obj.required_answer else 'No'
    
    def move_item(self, obj):
        if not obj.pk:
            return 'Not available before saving'
        strs = []
        if obj != ConsentItem.objects.first():
            strs.append((
                reverse('consent:move-item', kwargs = { 'pk': obj.pk, 'direction': 'up' }),
                'Up',
            ))
        if obj != ConsentItem.objects.last():
            strs.append((
                reverse('consent:move-item', kwargs = { 'pk': obj.pk, 'direction': 'down' }),
                'Down',
            ))
        return format_html_join(
            ' - ',
            '<a href="{}">[ {} ]</a>',
            strs
        )

@register(UserConsent)
class UserConsentAdmin(ModelAdmin):
    
    list_display = ('user','consented')
    readonly_fields = ('user',)