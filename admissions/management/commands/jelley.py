from django.core.management.base import BaseCommand, CommandError

from admissions.models import *

class Command(BaseCommand):
  help = 'Recalculate Jelley scores and ranks'

  def add_arguments(self, parser):
    parser.add_argument('tag', nargs='?', default='test')

  def handle(self, *args, **options):
    weights = Weights.objects.last()
    all_students = Candidate.objects.all()
    for s in all_students:
      s.stored_jell_score = s.calc_jell_score(weights)
      s.save()
      self.stdout.write('Jelley score of {0} is {1}'.format(s.ucas_id, s.stored_jell_score))
    ordered = Candidate.objects.order_by('-stored_jell_score').all()
    first = True
    index = 1
    for s in ordered:
      if first:
        s.stored_rank = index
        previous_score = s.stored_jell_score
        previous_rank = index
        first = False
      else:
        if s.stored_jell_score == previous_score:
          s.stored_rank = previous_rank
        else:
          s.stored_rank = index
          previous_score = s.stored_jell_score
          previous_rank = index
      s.save()
      self.stdout.write('Rank of {0} is {1} ({2})'.format(s.ucas_id, s.stored_rank, index))
      index = index + 1

