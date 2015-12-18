from django.core.management.base import BaseCommand, CommandError

from admissions.models import *
from admissions.views import ranked_offers

class Command(BaseCommand):
  help = 'Finalize highest-priority offers'

  def handle(self, *args, **options):
    for c in Candidate.objects.all().prefetch_related('offer'):
      s = ranked_offers(c)
      if s == '':
        continue # no offers
      offers = s.split()
      for offer in offers:
        if offer[0] == '(':
          continue # promoted
        elif offer[0] == 'P':
          # physphil offer
          course_type = Candidate.COURSE_PHYSPHIL_ONLY
        elif offer[0] == '3':
          # physics offer
          course_type = Candidate.COURSE_THREEYEAR
        elif offer[0] == '4':
          course_type = Candidate.COURSE_FOURYEAR
        else:
          self.stderr.write("Unrecognized offer string {0}".format(offer))
          break
        try:
          col = College.objects.get(adss_code=offer[2:5])
        except ObjectDoesNotExist:
          self.stderr.write("College code {0} unrecognized".format(offer[2:5]))
          continue
        try:
          offobj = Offer.objects.get(college=col, candidate=c, course_type=course_type)
        except ObjectDoesNotExist:
          self.stderr.write("Offer not found:  {0}[{1}] {2}".format(course_type, col.adss_code, c.ucas_id))
          continue
        except:
          self.stderr.write("Error locating offer:  {0}[{1}] {2}".format(course_type, col.adss_code, c.ucas_id))
          continue
        offobj.final = True
        offobj.save()
        self.stdout.write("   offer string:  {0}".format(offers))
        self.stdout.write("Offer finalized:  {0}[{1}] {2}".format(course_type, col.adss_code, c.info.surname))
        break # only process the first valid offer found

