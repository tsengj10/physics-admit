from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

import csv
import random
import string

from admissions.models import College

class Command(BaseCommand):
  help = 'Generate new keys in a new college table'

  def handle(self, *args, **options):
    f = open('college-table.csv', 'w')
    out = csv.writer(f, quoting=csv.QUOTE_ALL)
    row = []
    row.append("name")
    row.append("adss_code")
    row.append("total_places")
    row.append("physphil_places")
    row.append("key")
    out.writerow(row)
    for c in College.objects.all():
      row = []
      row.append(c.name)
      row.append(c.adss_code)
      row.append(c.total_places)
      row.append(c.physphil_places)
      row.append(id_generator())
      out.writerow(row)
    f.close()

def id_generator(size=16, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

