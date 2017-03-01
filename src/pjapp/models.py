from __future__ import unicode_literals

import re
import random
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import strip_tags, format_html_join
from django.utils.safestring import mark_safe
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from autoslug import AutoSlugField

@python_2_unicode_compatible
class Tag(models.Model):
    text = models.CharField(max_length=200, db_index=True, unique=True)
    
    class Meta:
        ordering = ['text']
          
    def __str__(self):
        return self.text

@python_2_unicode_compatible
class BaseTitleDescriptionTagModel(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    description = RichTextUploadingField(blank=True)
    date_created = models.DateTimeField(null=False, db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(null=True, db_index=True, auto_now=True)
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        db_index=True
    )
    annotations = models.TextField(
        blank = True,
        help_text = 'Your annotations will only be seen by you',
        verbose_name = 'My annotations (private)',
    )
    _tag_list = None
    
    def get_description_html(self):
        return mark_safe(self.description)
    
    def get_description_text(self):
        return strip_tags(self.description)
    
    @property
    def tag_list(self):
        if self._tag_list is None:
            if self.pk:
                self._tag_list = [tag.text for tag in self.tags.all()]
            else:
                self._tag_list = []
        return self._tag_list
    
    @tag_list.setter
    def tag_list(self, value):
        self._tag_list = value
    
    @property
    def flat_tag_list(self):
        return (",").join(self.tag_list)
    
    @flat_tag_list.setter
    def flat_tag_list(self, value):
        tags = [t.strip() for t in value.split(",")]
        self.tag_list = [t for t in tags if t]
    
    def save(self, *args, **kwargs):
        super(BaseTitleDescriptionTagModel, self).save(*args, **kwargs)
        new_tag_list = self.tag_list
        old_tag_list = [tag.text for tag in self.tags.all()]
        for tag in old_tag_list:
            if tag not in new_tag_list:
                self.tags.get(text=tag).delete()
        for tag in new_tag_list:
            if tag not in old_tag_list:
                tagobj, created = Tag.objects.get_or_create(text=tag)
                self.tags.add(tagobj)
    
    def __str__(self):
        return self.title
    
    class Meta:
        abstract = True

class Project(BaseTitleDescriptionTagModel):
    creator = models.ForeignKey(User, db_index=True, null=False, blank=False)
    
    class Meta:
        ordering = ['-date_created']
        
    def get_absolute_url(self):
        return reverse('pjapp:author:explore_project', kwargs={'pk': self.pk})

class Activity(BaseTitleDescriptionTagModel):
    project = models.ForeignKey(Project, related_name='activities', db_index=True, null=False, blank=False)
    
    class Meta:
        ordering = ['date_created']
        verbose_name_plural = 'Activities'
        
    def get_absolute_url(self):
        return reverse('pjapp:author:explore_activity', kwargs={'pk': self.pk})

class PathPosition(models.Model):
    path = models.ForeignKey('Path', related_name='positions', db_index=True, null=False, blank=False)
    activity = models.ForeignKey(Activity, related_name='positions', db_index=True, null=False, blank=False)
    block_position_x = models.PositiveSmallIntegerField(db_index=True, null=True, default=0)
    block_position_y = models.PositiveSmallIntegerField(db_index=True, null=True, default=0)
    
    class Meta:
        ordering = ['block_position_y', 'block_position_x']

def make_slug(obj):
    return '%s %s'%(obj.title, '%06x'%(random.randrange(0x1000000)))

class Path(BaseTitleDescriptionTagModel):
    listed_publicly = models.BooleanField(
        default=False,
        help_text="If checked, it will appear on the app's directory. If unchecked, trajectory will be accessible to users who have the URL"
    )
    project = models.ForeignKey(Project, related_name='paths', db_index=True, null=False, blank=False)
    slug = AutoSlugField(null=True, default=None, unique=True, populate_from=make_slug)
    
    class Meta:
        ordering = ['-date_created']
        
    def get_absolute_url(self):
        return reverse('pjapp:author:explore_path', kwargs={'pk': self.pk})
        
    def get_activities(self):
        return Activity.objects.filter(
                                       positions__path = self
                                       ).distinct()
    
    def get_unused_activities(self):
        return Activity.objects.filter(
                                       project = self.project
                                       ).exclude(
                                       positions__path = self
                                       ).distinct()
    
    def rebuild_positions(self):
        PathPosition.objects.filter(path=self).delete()
        used_links = []
        activity_positions = {}
        from_start = self.links.filter(from_activity=None)
        countery = 0
        activity_count = Activity.objects.filter(
                                                 models.Q(forward_links__path=self)
                                                 | models.Q(backward_links__path=self)
                                                 ).distinct().count()
        while from_start.count():
            countery += 1
            activity_ids = []
            for link in from_start:
                if link.to_activity is not None:
                    id = link.to_activity_id
                    if id not in activity_positions:
                        activity_positions[id] = {
                            'y': countery,
                            'id': id
                        }
                        if link.from_activity is not None and link.from_activity_id in activity_positions:
                            activity_positions[id]['x'] = activity_positions[link.from_activity_id]['x']
                        else:
                            activity_positions[id]['x'] = -1
                        activity_ids.append(id)
                used_links.append(link.id)
            line_positions = [activity_positions[p] for p in activity_positions if activity_positions[p]['y'] == countery]
            line_positions.sort(key=lambda p: p['x'])
            counterx = 0
            for p in line_positions:
                counterx += 1
                p['x'] = counterx
            from_start = self.links.filter(
                                           models.Q(from_activity_id__in=activity_ids)
                                           & ~models.Q(to_activity=None)
                                           & ~models.Q(id__in=used_links)
                                           )
            if countery > activity_count:
                break
        unused_links = self.links.exclude(id__in=used_links).distinct()
        unused_activities = []
        for link in unused_links:
            if (link.from_activity is not None) and (link.from_activity_id not in activity_positions) and (link.from_activity_id not in unused_activities):
                unused_activities.append(link.from_activity_id)
            if (link.to_activity is not None) and (link.to_activity_id not in activity_positions) and (link.to_activity_id not in unused_activities):
                unused_activities.append(link.to_activity_id)
        for activity_id in activity_positions:
            pos = activity_positions[activity_id]
            PathPosition.objects.create(
                activity_id = activity_id,
                path = self,
                block_position_x = pos['x'],
                block_position_y = pos['y'],
            )
        for activity_id in unused_activities:
            PathPosition.objects.create(
                activity_id = activity_id,
                path = self,
                block_position_x = None,
                block_position_y = None,
            )

@python_2_unicode_compatible
class PathLink(models.Model):
    path = models.ForeignKey(Path, related_name='links', db_index=True, null=False, blank=False)
    from_activity = models.ForeignKey(Activity, related_name='forward_links', db_index=True, null=True, blank=True)
    to_activity = models.ForeignKey(Activity, related_name='backward_links', db_index=True, null=True, blank=True)
    date_created = models.DateTimeField(null=False, db_index=True, auto_now_add=True)
    date_updated = models.DateTimeField(null=True, db_index=True, auto_now=True)
    
    class Meta:
        unique_together = (
                           ('path', 'from_activity', 'to_activity'),
                           )
    
    def get_from_activity_title(self):
        return self.from_activity.title if self.from_activity else "Start of trajectory"
    
    def get_to_activity_title(self):
        return self.to_activity.title if self.to_activity else "End of trajectory"
    
    def __str__(self):
        return 'From %s to %s'%(self.get_from_activity_title(), self.get_to_activity_title())
    
    def clean(self):
        if self.from_activity and self.from_activity.project != self.project:
            raise ValidationError("Previous activity and path must be in the same project")
        if self.to_activity and self.to_activity.project != self.project:
            raise ValidationError("Next activity and path must be in the same project")

@python_2_unicode_compatible
class CustomActivity(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    project = models.ForeignKey(Project, db_index=True, null=False, blank=False)
    title = models.CharField(max_length=200, default='Untitled Activity')
    description = models.TextField(blank=True)
    
    def get_description_html(self):
        description_lines = re.split(r"[\r\n]+", self.description)
        description_lines = [(line.strip(),) for line in description_lines if line.strip()]
        return format_html_join('\n','<p>{}</p>', description_lines)
    
    def get_description_text(self):
        return self.description
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = 'Custom activities'

@python_2_unicode_compatible
class RecordedPath(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    path = models.ForeignKey(Path, related_name='recorded_instances', db_index=True, null=False, blank=False)
    title = models.CharField(max_length=200)
    date_started = models.DateTimeField(null=False, db_index=True, auto_now_add=True)
    date_ended = models.DateTimeField(null=True, blank=True, db_index=True)
    
    class Meta:
        ordering = ['-date_started']
    
    def get_absolute_url(self):
        return reverse('pjapp:author:review_path', kwargs={'pk': self.pk})
    
    def is_ongoing(self):
        return (self.date_ended is None)
    is_ongoing.boolean = True
    
    def get_status(self):
        return 'Ongoing' if self.is_ongoing() else 'Finished'
    
    def get_total_activities(self):
        return self.path.get_activities().count()
    
    def get_done_activities(self):
        return Activity.objects.filter(steps__recorded_path=self).distinct().count()
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title =  self.path.title
        super(RecordedPath, self).save(*args, **kwargs)
    
    def __str__(self):
        return "%s taken by %s"%(self.title, self.user.username)

@python_2_unicode_compatible
class RecordedStep(models.Model):
    STEP_IN_PROGRESS = 'P'
    STEP_SKIPPED = 'S'
    STEP_DONE = 'D'
    STEP_STATUSES = (
                     ( STEP_IN_PROGRESS, 'In progress' ),
                     ( STEP_SKIPPED, 'Skipped' ),
                     ( STEP_DONE, 'Done' ),
                     )
    activity = models.ForeignKey(Activity, related_name='steps', db_index=True, null=True, blank=True, default=None)
    custom_activity = models.ForeignKey(CustomActivity, related_name='steps', db_index=True, null=True, blank=True, default=None)
    recorded_path = models.ForeignKey(RecordedPath, related_name='steps', db_index=True, null=False, blank=False)
    status = models.CharField(max_length=1, db_index=True, null=False, blank=False, choices=STEP_STATUSES, default=STEP_IN_PROGRESS)
    date_started = models.DateTimeField(null=False, db_index=True, auto_now_add=True)
    date_ended = models.DateTimeField(null=True, blank=True, db_index=True)
    next_step = models.OneToOneField('RecordedStep', related_name='previous_step', db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    path_index = models.PositiveSmallIntegerField(default=0)
    is_canonical = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['recorded_path', 'path_index']
    
    def has_custom_activity(self):
        return (not self.activity_id)
    has_custom_activity.boolean = True
    has_custom_activity.short_description = 'Custom?'
    
    def get_activity(self):
        return self.custom_activity if self.has_custom_activity() else self.activity
    get_activity.short_description = 'Activity'
    
    def is_on_trajectory(self):
        if self.has_custom_activity():
            return False
        rp = self.recorded_path
        return (self.activity in rp.path.get_activities())
    is_on_trajectory.boolean = True
    
    def __str__(self):
        return "%s in %s"%(self.get_activity().title, self.recorded_path)

@python_2_unicode_compatible
class Comment(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    activity = models.ForeignKey(Activity, related_name='comments', db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    custom_activity = models.ForeignKey(CustomActivity, related_name='comments', db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    recorded_path = models.ForeignKey(RecordedPath, related_name='comments', db_index=True, null=True, blank=True, default=None, on_delete=models.SET_NULL)
    rating = models.PositiveSmallIntegerField(default=0)
    content = models.TextField(blank=True, default='')
    image = models.ImageField(blank=True)
    date_created = models.DateTimeField(null=False, db_index=True, auto_now_add=True)
    public = models.BooleanField(db_index=True, default=False)
    
    class Meta:
        ordering = ['-date_created']
            
    def __str__(self):
        return 'Comment by %s at %s'%(self.user.username, self.date_created)
