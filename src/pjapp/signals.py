from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from pjapp.models import Activity, Path, PathLink

@receiver(post_save, sender=PathLink)
@receiver(post_delete, sender=PathLink)
def rebuild_positions(sender, instance, **kwargs):
    instance.path.rebuild_positions()
    instance.path.save()

@receiver(post_save, sender=Path)
@receiver(post_delete, sender=Path)
@receiver(post_save, sender=Activity)
@receiver(post_delete, sender=Activity)
def keep_track_of_project_change(sender, instance, **kwargs):
    instance.project.save()