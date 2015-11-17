from django.core.management.base import BaseCommand, CommandError

from admissions.models import *
from admissions.fixtures.scores import scores

class Command(BaseCommand):
  help = 'Check PAT details'

  def handle(self, *args, **options):
    for i in range(0,len(scores)):
      m = i + 1
      k = "q{0}".format(m)
      self.stdout.write(k)
      v = [ p for p in PATDetails.objects.all()
                    if int(getattr(p,k)) > scores[i] ]
      for w in v:
        self.stdout.write("{0} {1}: {2} max {3} ({4}, {5})".format(
            k, w.candidate.ucas_id, int(getattr(w,k)), scores[i],
            w.candidate.info.surname, w.candidate.info.forenames))

