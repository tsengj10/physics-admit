from django.core.management.base import BaseCommand, CommandError

import csv
import sys
from random import randint

from admissions.models import *

def append_unique(a, v):
  if v != None and v not in a:
    a.append(v)

def choose(n, initialvals, choices):
  vals = initialvals
  while len(vals) < n:
    p = randint(0, len(choices) - 1)
    v = choices[p]
    if v not in vals:
      vals.append(v)
  return vals

class Command(BaseCommand):
  help = "Assign random colleges beyond preselected ones"
    
  def handle(self, *args, **options):
    out = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    fields = [ 'ucas_id','college3','college4','college5','college6' ]
    out.writerow(fields)

    colleges = College.objects.filter(total_places__gt=0)
    cpks = [c.adss_code for c in colleges]
    cppks = [c.adss_code for c in College.objects.filter(physphil_places__gt=0)]
    self.stdout.write("{0} colleges, of which {1} offer physphil".format(len(cpks), len(cppks)))

    for s in Candidate.objects.filter(state=Candidate.STATE_SUMMONED):
      pp = (s.course_type == Candidate.COURSE_PHYSPHIL_ONLY or
            s.course_type == Candidate.COURSE_PHYSPHIL_WITH_FALLBACK)
      base = 0
      ivals = []
      if s.college_selected != s.college1:
        base = 1
        append_unique(ivals, s.college_selected.adss_code)
      append_unique(ivals, s.college1.adss_code)
      append_unique(ivals, s.college2.adss_code)

      if pp:
        vals = choose(base+6, ivals, cppks)
      else:
        vals = choose(base+6, ivals, cpks)

      data = [ s.ucas_id, vals[base+2], vals[base+3], vals[base+4], vals[base+5] ]
      out.writerow(data)

