from django.core.management.base import BaseCommand, CommandError

from admissions.models import *
from admissions.fixtures.scores import scores, list_maths, list_physics

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

    for c in Candidate.objects.all():
      p = c.pat
      pm = 0
      pp = 0
      for n in list_maths:
        k = "q{0}".format(n)
        pm = pm + int(getattr(p,k))
      for n in list_physics:
        k = "q{0}".format(n)
        pp = pp + int(getattr(p,k))
      if pm != c.pat_maths or pp != c.pat_physics:
        print("{0}:  values {1} {2} sums {3} {4}".format(c.ucas_id,
              c.pat_maths, c.pat_physics, pm, pp))

