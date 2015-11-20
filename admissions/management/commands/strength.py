from django.core.management.base import BaseCommand, CommandError

from admissions.models import *

class Command(BaseCommand):
  help = 'Calculate list strength for each college'

  def handle(self, *args, **options):
    for c in College.objects.all():
      n = c.total_places
      if n == 0:
        continue
      scores = []
      for s in c.college1.all():
        if s.offer.count() == 0:
          scores.append(float(s.pat_physics) + float(s.pat_maths))
      scores.sort(reverse=True)
      top = scores[:n]
      avg = float(sum(top)) / float(len(top))
      self.stdout.write("{0}: {1} places out of {2} candidates, strength {3}".format(c.adss_code, len(top), len(scores), avg))

