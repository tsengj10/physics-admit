from django.core.management.base import BaseCommand, CommandError

from admissions.models import *

class Command(BaseCommand):
  help = 'Report on applicant cohort'

  def handle(self, *args, **options):
    eu = ['Austrian', 'Belgian', 'Bulgarian', 'Croatian',
          'Cypriot (European Union)', 'Czech', 'Danish', 'Estonian',
          'Finnish', 'French', 'German', 'Greek', 'Hungarian', 'Irish',
          'Italian', 'Latvian', 'Lithuanian', 'Luxembourger', 'Maltese',
          'Dutch', 'Polish', 'Portuguese', 'Romanian', 'Slovak',
          'Slovenian', 'Spanish', 'Swedish','Swiss']
    uk = ['UK national','Manx','Jersey','Guernsey']
    ntotal = 0
    nuk = 0
    neu = 0
    noverseas = 0
    nmale = 0
    nfemale = 0
    ntrans = 0
    nunknown = 0
    ndeferred = 0
    nshort = 0
    for c in CandidateInfo.objects.all():
      ntotal = ntotal + 1
      if c.gender == c.MALE:
        nmale = nmale + 1
      elif c.gender == c.FEMALE:
        nfemale = nfemale + 1
      elif c.gender == c.TRANSGENDER:
        ntrans = ntrans + 1
      else:
        nunknown = nunknown + 1
      if c.deferred_entry:
        ndeferred = ndeferred + 1
      if c.overseas:
        noverseas = noverseas + 1
      else:
        if c.current_passport_country in eu:
          neu = neu + 1
        else:
          nuk = nuk + 1
    self.stdout.write("Total number of candidates = {0}".format(ntotal))
    self.stdout.write("  Number of deferred entry = {0}".format(ndeferred))
    self.stdout.write("  Gender:")
    self.stdout.write("    Male                   = {0}".format(nmale))
    self.stdout.write("    Female                 = {0}".format(nfemale))
    self.stdout.write("    Transgender            = {0}".format(ntrans))
    self.stdout.write("    Unknown                = {0}".format(nunknown))
    self.stdout.write("  Domicile:")
    self.stdout.write("    Overseas               = {0}".format(noverseas))
    self.stdout.write("    Non-overseas EU/Swiss  = {0}".format(neu))
    self.stdout.write("    Non-overseas UK        = {0}".format(nuk))
    self.stdout.write("Shortlist:")
    self.stdout.write("  Total                    = {0}".format(Candidate.objects.filter(state=Candidate.STATE_SUMMONED).count()))

