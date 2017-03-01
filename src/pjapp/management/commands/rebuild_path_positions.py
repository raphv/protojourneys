from django.core.management.base import BaseCommand
from pjapp.models import Path

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        
        print("Rebuilding positions for %d paths"%Path.objects.count())
        counter = 1
        
        for path in Path.objects.all():
            print("%s: Rebuilding positions for path '%s'"%(
                str(counter).rjust(3),
                path.title.encode('ascii','ignore')
            ))
            path.rebuild_positions()
            counter += 1