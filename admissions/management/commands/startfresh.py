from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

import csv
from datetime import date

from admissions.models import *

class Command(BaseCommand):
  help = 'Start a new database instance from scratch'

  def handle(self, *args, **options):
    #load_college_table()
    #load_school_types()
    #load_qual_types()
    create_college_groups()
    # may want to load a user table as well
    ovs = OverallState(state=OverallState.DEVELOPMENT)
    ovs.save()

def load_college_table():
  firstline = 1
  with open('admissions/fixtures/college-table.csv','r') as csvfile:
    f = csv.reader(csvfile)
    for row in f:
      if firstline:
        firstline = 0
      else:
        p, created = College.objects.update_or_create(adss_code=row[1],
                       defaults={'name' : row[0],
                                 'total_places' : int(row[2]),
                                 'physphil_places' : int(row[3]),
                                 'key' : row[4]})
        if created:
          print('Created college {}'.format(p))
        else:
          print('Updated college {}'.format(p))

def load_school_types():
  firstline = 1
  with open('admissions/fixtures/school-types-phys.csv','r') as csvfile:
    f = csv.reader(csvfile)
    for row in f:
      if firstline:
        firstline = 0
      else:
        p, created = PhysicsSchoolType.objects.update_or_create(adss_type=row[0],
                       defaults={'adss_description' : row[1],
                                 'physics_type' : row[2]})
        if created:
          print('Created school type {}'.format(p))
        else:
          print('Updated school type {}'.format(p))

def toBoolean(str):
  if len(str) > 0:
    return str[0].lower() in [ 'y', 't' ]
  else:
    return False

def load_qual_types():
  firstline = 1
  with open('admissions/fixtures/qual-types.csv','r') as csvfile:
    f = csv.reader(csvfile)
    for row in f:
      if firstline:
        firstline = 0
      else:
        p, created = QualificationType.objects.update_or_create(name=row[0],
                       defaults={'exam_type' : row[1],
                                 'dual_award' : toBoolean(row[2]),
                                 'short_course' : toBoolean(row[3]),
                                 'short_name' : row[4]})
        if created:
          print('Created qualification type {}'.format(p))
        else:
          print('Updated qualification type {}'.format(p))

def create_college_groups():
  colleges = College.objects.all()
  for college in colleges:
    g = Group.objects.filter(name=college.adss_code)
    if g.count() == 0:
      g = Group(name=college.adss_code)
      g.save()
      print('Created user group "{1}" for "{0}"'.format(college, g))
  # and then add a read-only group
  g = Group.objects.filter(name='Readonly')
  if g.count() == 0:
    g = Group(name='Readonly')
    g.save()
    print('Created user group "Readonly"')

