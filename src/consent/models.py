from __future__ import unicode_literals

from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import strip_tags
from django.utils.text import Truncator
# Create your models here.

@python_2_unicode_compatible
class ConsentItem(models.Model):
    description = RichTextUploadingField(blank=False)
    position_index = models.PositiveSmallIntegerField(db_index=True)
    required_answer = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['position_index']
        
    def save(self, *args, **kwargs):
        if self.position_index is None:
            if ConsentItem.objects.count():
                self.position_index = (1 + ConsentItem.objects.last().position_index)
            else:
                self.position_index = 0
        return super(ConsentItem, self).save(*args, **kwargs)
    
    def swap_positions(self, other_widget):
        new_index = other_widget.position_index
        other_widget.position_index = self.position_index
        self.position_index = new_index
        other_widget.save()
        self.save()
    
    def move_up(self):
        widgets_before = ConsentItem.objects.filter(position_index__lt=self.position_index)
        if widgets_before.count():
            self.swap_positions(widgets_before.last())
    
    def move_down(self):
        widgets_after = ConsentItem.objects.filter(position_index__gt=self.position_index)
        if widgets_after.count():
            self.swap_positions(widgets_after.last())
    
    def __str__(self):
        return Truncator(strip_tags(self.description)).chars(60)

class UserConsent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    consented = models.BooleanField(default=False)