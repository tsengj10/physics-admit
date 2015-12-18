from django.core.management.base import BaseCommand, CommandError

import csv
import sys

from admissions.models import *

class Command(BaseCommand):
  output_transaction = True
  help = "Export offer information to stdout in csv form"
    
  def handle(self, *args, **options):
    out = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    fields = [ 'ucas_id','college','course_type','deferred','open','surname','forenames' ]
    out.writerow(fields)

    for o in Offer.objects.filter(final=True).order_by('candidate__ucas_id'):
      c = o.college
      s = o.candidate
      i = s.info
      if o.course_type == '3':
        ct = 'BA'
      elif o.course_type == '4':
        ct = 'MPhys'
      elif o.course_type == 'P':
        ct = 'MPhysPhil'
      else:
        ct = 'Undefined'
      data = [ s.ucas_id, c.adss_code, ct, o.deferred_entry, o.underwritten, i.surname, i.forenames, ]
      out.writerow(data)

