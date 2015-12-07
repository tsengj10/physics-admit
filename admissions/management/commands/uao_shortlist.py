from django.core.management.base import BaseCommand, CommandError

import csv
import sys

from admissions.models import *

class Command(BaseCommand):
  output_transaction = True
  help = "Export candidate information to stdout in csv form"
    
  def handle(self, *args, **options):
    out = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    fields = [ 'ucas_id','surname','forenames','pat_total','college1','college2' ]
    out.writerow(fields)

    for s in Candidate.objects.all().select_related('info'):
      c = s.info
      pt = s.pat_physics + s.pat_maths
      if s.state == s.STATE_SUMMONED:
        decision = s.college1.adss_code
        college2 = s.college2.adss_code
      elif s.state == s.STATE_WITHDRAWN:
        decision = 'Withdrawn'
        college2 = ''
      else:
        decision = 'Desummoned'
        college2 = ''

      data = [ s.ucas_id, c.surname, c.forenames, pt, decision, college2 ]
      out.writerow(data)

