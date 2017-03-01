from django import template
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()

@register.filter
def star_rating(value):
    stars = []
    intval = int(value)
    if intval:
        for n in range(5):
            cls = 'fa-star' if intval > n else 'fa-star-o'
            attrs = mark_safe('class="fa %s"'%cls)
            stars.append((attrs,))
        return format_html_join('\n','<i {}></i>',stars)
    else:
        return ''

@register.simple_tag
def login_url():
    return settings.LOGIN_URL