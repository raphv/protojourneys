from __future__ import unicode_literals

from django.apps import AppConfig

class PjappConfig(AppConfig):
    name = 'pjapp'
    verbose_name = 'Protojourneys app'
    
    def ready(self):
        import pjapp.signals
